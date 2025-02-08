import os
import torch
import torchaudio
from transformers import pipeline, WhisperProcessor, WhisperForConditionalGeneration
import numpy as np
from glob import glob

def load_model(model_id, cache_dir):
    """
    Load the Whisper ASR model with given model ID and cache directory.
    """
    print(f"[INFO] Loading model '{model_id}' with cache directory '{cache_dir}'.")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[INFO] Using device: {device}.")
    torch_dtype = torch.float16

    processor = WhisperProcessor.from_pretrained(model_id, torch_dtype=torch_dtype, cache_dir=cache_dir)
    model = WhisperForConditionalGeneration.from_pretrained(model_id, torch_dtype=torch_dtype, cache_dir=cache_dir).to(device)

    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        return_timestamps=True,
        torch_dtype=torch_dtype,
        device=device,
        return_language=True
    )
    print("[INFO] Model loaded successfully.")
    return pipe

def detect_non_silent(audio, sr=16000, silence_db=-40, min_silence_len_sec=1, min_gap_sec=1, min_duration_sec=0.05):
    """
    Detect non-silent segments in an audio array and merge short pauses.
    """
    print("[INFO] Detecting non-silent segments in audio.")
    if len(audio) == 0:
        print("[WARN] Audio array is empty. No segments detected.")
        return []

    db_audio = 20 * np.log10(np.abs(audio) + 1e-10)
    silent = (db_audio < silence_db)

    segments, start, is_silent = [], 0, silent[0]
    for i in range(1, len(silent)):
        if silent[i] != is_silent:
            segments.append((is_silent, start, i))
            start, is_silent = i, silent[i]
    segments.append((is_silent, start, len(silent)))

    non_silent_segments = [(s / sr, e / sr) for is_silent, s, e in segments if not is_silent]

    merged_segments = []
    if non_silent_segments:
        prev_start, prev_end = non_silent_segments[0]
        for start, end in non_silent_segments[1:]:
            if start - prev_end <= min_gap_sec:
                prev_end = end
            else:
                merged_segments.append((prev_start, prev_end))
                prev_start, prev_end = start, end
        merged_segments.append((prev_start, prev_end))

    filtered_segments = [(s, e) for s, e in merged_segments if e - s >= min_duration_sec]
    print(f"[INFO] Detected {len(filtered_segments)} non-silent segments.")
    return filtered_segments

def audio_normalize(audio):
    """
    Normalize an audio waveform to -20dB RMS.
    """
    print("[INFO] Normalizing audio.")
    waveform, sample_rate = audio
    waveform = waveform.squeeze().numpy()
    rms = np.sqrt(np.mean(waveform**2))
    target_rms = 10 ** (-20 / 20)
    if rms > 0:
        waveform *= target_rms / rms
    print("[INFO] Audio normalization complete.")
    return waveform, sample_rate

def extract_timestamps(timestamps, waveform, cache_dir, samplerate=16000, model_id="waveletdeboshir/whisper-large-v3-no-numbers"):
    """
    Extract precise timestamps from non-silent audio segments.
    If a segment requires more than 10 chunks to process, skip that segment.
    """
    print("[INFO] Extracting precise timestamps from non-silent segments.")
    pipe = load_model(model_id, cache_dir)
    refined_timestamps = []

    for segment_index, (start, end) in enumerate(timestamps):
        print(f"[INFO] Processing segment {segment_index+1}: from {start:.2f} to {end:.2f} seconds.")
        segment = waveform[int(start * samplerate):int(end * samplerate)]
        savetime, temp_timestamps = 0, []
        chunk_count = 0

        while len(segment) / samplerate >= 30 or savetime == 0:
            chunk_count += 1
            if chunk_count > 30:
                print(f"[WARN] Segment {segment_index+1} exceeded 30 chunks; skipping this segment.")
                temp_timestamps = []  # Discard partial results
                break
            print(f"[INFO] Processing chunk {chunk_count} of segment {segment_index+1}.")
            chunk = segment[:30 * samplerate]
            result = pipe(chunk, generate_kwargs={
                "num_beams": 1,
                "temperature": 0.0,
                "return_timestamps": True,
                "task": "transcribe"
            })
            if not result['chunks']:
                print("[WARN] No transcription chunks found in current chunk.")
                break

            for i in result['chunks']:
                if i['timestamp'] and i['timestamp'][0] is not None and i['timestamp'][1] is not None and i['timestamp'][0] < i['timestamp'][1] < 30:
                    temp_timestamps.append((i['timestamp'][0] + savetime, i['timestamp'][1] + savetime))
                    savetime = i['timestamp'][1]

            segment = segment[int(savetime * samplerate):]

        if chunk_count > 10:
            # Skip adding timestamps for this segment if chunk limit exceeded
            print(f"[INFO] Skipping segment {segment_index+1} due to excessive chunk count.")
            continue

        print(f"[INFO] Extracted {len(temp_timestamps)} timestamps from segment {segment_index+1}.")
        refined_timestamps += [(start + ts[0], start + ts[1]) for ts in temp_timestamps]

    print("[INFO] Timestamp extraction complete.")
    return refined_timestamps

def save_slices(info, wav_output_dir):
    """
    Save sliced audio segments and corresponding transcriptions.
    """
    idx = 0
    print("[INFO] Saving sliced audio segments.")
    for (wavfile, timestamps) in info:
        print(f"[INFO] Saving slices for file: {wavfile}")
        waveform, sample_rate = torchaudio.load(wavfile)
        waveform = waveform.mean(dim=0, keepdim=True) if waveform.shape[0] > 1 else waveform

        for (start, end) in timestamps:
            sliced_waveform = waveform[:, int(start * sample_rate):int(end * sample_rate)]
            output_path = os.path.join(wav_output_dir, f"{str(idx).zfill(5)}.wav")
            torchaudio.save(output_path, sliced_waveform, sample_rate)
            idx+=1
            print(f"[INFO] Saved slice to {output_path}.")

        os.remove(wavfile)
        parts = os.path.normpath(wavfile).split(os.sep)
        parts[-2] = "audio_wav"
        parts[-1] = parts[-1][:-3]+"wav"
        os.remove(os.path.join(*parts))
        print(f"[INFO] Removed original file: {wavfile}.")
        print(f"[INFO] Removed original file: {os.path.join(*parts)}.")
    print("[INFO] All slices saved.")

def process_audio_files(input_folder, output_dir, cache_dir, model_id):
    """
    Process all audio files in a directory, detect speech, and save results.
    """
    print(f"[INFO] Starting processing of audio files in folder: {input_folder}.")
    info = []
    file_list = glob(os.path.join(input_folder, "*.mp3"))
    print(f"[INFO] Found {len(file_list)} audio files.")

    for wav_file in file_list:
        print(f"[INFO] Processing file: {wav_file}.")
        audio = torchaudio.load(wav_file)
        normalized_audio, _ = audio_normalize(audio)

        timestamps = detect_non_silent(normalized_audio)
        print(f"[INFO] Detected {len(timestamps)} non-silent segments in file: {wav_file}.")

        timestamps = extract_timestamps(timestamps, normalized_audio, cache_dir, model_id=model_id)
        print(f"[INFO] Refined to {len(timestamps)} timestamps after extraction for file: {wav_file}.")

        info.append((wav_file, timestamps))
        print(f"[INFO] Finished processing file: {wav_file}.")

    print("[INFO] Saving slices for all processed files.")
    save_slices(info, output_dir)
    print("[INFO] Audio processing completed.")
