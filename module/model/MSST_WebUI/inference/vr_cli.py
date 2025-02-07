import argparse
import warnings
import logging
from time import time
from modules.vocal_remover.separator import Separator
from utils.logger import get_logger

def vr_inference(args):
    logger = get_logger(console_level=logging.INFO)

    if not args.debug:
        warnings.filterwarnings("ignore", category=UserWarning)

    start_time = time()

    separator = Separator(
        logger=logger,
        debug=args.debug,
        model_file=args.model_path,
        output_dir=args.output_folder,
        output_format=args.output_format,
        invert_using_spec=args.invert_spect,
        use_cpu=args.use_cpu,
        vr_params={
            "batch_size": args.batch_size,
            "window_size": args.window_size,
            "aggression": args.aggression,
            "enable_tta": args.enable_tta,
            "enable_post_process": args.enable_post_process,
            "post_process_threshold": args.post_process_threshold,
            "high_end_process": args.high_end_process,
        },
    )
    success_files = separator.process_folder(args.input_folder)
    separator.del_cache()
    logger.info(f"Successfully separated files: {success_files}, total time: {time() - start_time:.2f} seconds.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vocal Remover Command Line Interface", formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, max_help_position=60))

    parser.add_argument("-d", "--debug", action='store_true', help="Enable debug logging (default: %(default)s). Example: --debug")
    parser.add_argument("--use_cpu", action="store_true", help="Use CPU instead of GPU for inference (default: %(default)s). Example: --use_cpu")

    io_params = parser.add_argument_group("Separation I/O Params")
    io_params.add_argument("-i", "--input_folder", type=str, help="Folder with mixtures to process. [required]")
    io_params.add_argument("-o", "--output_folder", default="results", help="Folder to store separated files. str for single folder, dict with instrument keys for multiple folders. Example: --output_folder=results or --output_folder=\"{'vocals': 'results/vocals', 'instrumental': 'results/instrumental'}\"")
    io_params.add_argument("--output_format", choices=['wav', 'flac', 'mp3'], default="wav", help="Output format for separated files (default: %(default)s). Example: --output_format=wav")

    common_params = parser.add_argument_group("Common Separation Parameters")
    common_params.add_argument("-m", "--model_path", type=str, help="Path to model checkpoint. [required]")
    common_params.add_argument("--invert_spect", action="store_true", help="Invert secondary stem using spectogram (default: %(default)s). Example: --invert_spect")

    vr_params = parser.add_argument_group("VR Architecture Parameters")
    vr_params.add_argument("--batch_size", type=int, default=2, help="Number of batches to process at a time. higher = more RAM, slightly faster processing (default: %(default)s). Example: --batch_size=16")
    vr_params.add_argument("--window_size", type=int, default=512, help="Balance quality and speed. 1024 = fast but lower, 320 = slower but better quality. (default: %(default)s). Example: --window_size=320")
    vr_params.add_argument("--aggression", type=int, default=5, help="Intensity of primary stem extraction, -100 - 100. typically 5 for vocals & instrumentals (default: %(default)s). Example: --aggression=2")
    vr_params.add_argument("--enable_tta", action="store_true", help="Enable Test-Time-Augmentation; slow but improves quality (default: %(default)s). Example: --enable_tta")
    vr_params.add_argument("--high_end_process", action="store_true", help="Mirror the missing frequency range of the output (default: %(default)s). Example: --high_end_process")
    vr_params.add_argument("--enable_post_process", action="store_true", help="Identify leftover artifacts within vocal output; may improve separation for some songs (default: %(default)s). Example: --enable_post_process")
    vr_params.add_argument("--post_process_threshold", type=float, default=0.2, help="Threshold for post_process feature: 0.1-0.3 (default: %(default)s). Example: --post_process_threshold=0.1")

    args = parser.parse_args()
    vr_inference(args)