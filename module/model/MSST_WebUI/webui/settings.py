import os
import shutil
import gradio as gr
import requests
import webbrowser
import traceback

from utils.constant import *
from webui.utils import i18n, load_configs, save_configs, load_msst_model, load_vr_model, load_selected_model, logger

def reset_settings():
    config = load_configs(WEBUI_CONFIG)
    config_backup = load_configs(WEBUI_CONFIG_BACKUP)
    for key in config_backup['settings'].keys():
        config['settings'][key] = config_backup['settings'][key]
    save_configs(config, WEBUI_CONFIG)
    logger.info(f"Reset settings: {config['settings']}")
    return i18n("设置重置成功, 请重启WebUI刷新! ")

def reset_webui_config():
    config = load_configs(WEBUI_CONFIG)
    config_backup = load_configs(WEBUI_CONFIG_BACKUP)
    for key in config_backup['training'].keys():
        config['training'][key] = config_backup['training'][key]
    for key in config_backup['inference'].keys():
        config['inference'][key] = config_backup['inference'][key]
    for key in config_backup['tools'].keys():
        config['tools'][key] = config_backup['tools'][key]
    save_configs(config, WEBUI_CONFIG)
    logger.info(f"Reset webui config: {config}")
    return i18n("记录重置成功, 请重启WebUI刷新! ")

def save_uvr_modeldir(select_uvr_model_dir):
    if not os.path.exists(select_uvr_model_dir):
        return i18n("请选择正确的模型目录")
    config = load_configs(WEBUI_CONFIG)
    config['settings']['uvr_model_dir'] = select_uvr_model_dir
    save_configs(config, WEBUI_CONFIG)
    logger.info(f"Saved UVR model dir: {select_uvr_model_dir}")
    return i18n("设置保存成功! 请重启WebUI以应用。")

def check_webui_update():
    try:
        response = requests.get(UPDATE_URL)
        response.raise_for_status()
        latest_version = response.url.split("/")[-1]
        if latest_version != PACKAGE_VERSION:
            return i18n("当前版本: ") + PACKAGE_VERSION + i18n(", 发现新版本: ") + latest_version
        else:
            return i18n("当前版本: ") + PACKAGE_VERSION + i18n(", 已是最新版本")
    except Exception as e:
        logger.error(f"Fail to check update. Error: {e}\n{traceback.format_exc()}")
        return i18n("检查更新失败")

def webui_goto_github():
    webbrowser.open(UPDATE_URL)

def change_language(language):
    config = load_configs(WEBUI_CONFIG)
    language_dict = load_configs(LANGUAGE)
    if language in language_dict.keys():
        config['settings']['language'] = language_dict[language]
    else:
        config['settings']['language'] = "Auto"
    save_configs(config, WEBUI_CONFIG)
    logger.info(f"Change language to: {language}")
    return i18n("语言已更改, 重启WebUI生效")

def save_port_to_config(port):
    port = int(port)
    config = load_configs(WEBUI_CONFIG)
    config['settings']['port'] = port
    save_configs(config, WEBUI_CONFIG)
    logger.info(f"Saved port: {port}")
    return i18n("成功将端口设置为") + str(port) + i18n(", 重启WebUI生效")

def change_download_link(link):
    config = load_configs(WEBUI_CONFIG)
    if link == i18n("huggingface.co (需要魔法)"):
        config['settings']['download_link'] = "huggingface.co"
    elif link == i18n("hf-mirror.com (镜像站可直连)"):
        config['settings']['download_link'] = "hf-mirror.com"
    else:
        config['settings']['download_link'] = "Auto"
    logger.info(f"Change download link to: {link}")
    save_configs(config, WEBUI_CONFIG)
    return i18n("下载链接已更改")

def change_share_link(flag):
    config = load_configs(WEBUI_CONFIG)
    if flag:
        config['settings']['share_link'] = True
        save_configs(config, WEBUI_CONFIG)
        logger.info("Share link is enabled")
        return i18n("公共链接已开启, 重启WebUI生效")
    else:
        config['settings']['share_link'] = False
        save_configs(config, WEBUI_CONFIG)
        logger.info("Share link is disabled")
        return i18n("公共链接已关闭, 重启WebUI生效")

def change_local_link(flag):
    config = load_configs(WEBUI_CONFIG)
    if flag:
        config['settings']['local_link'] = True
        save_configs(config, WEBUI_CONFIG)
        logger.info("Local link is enabled")
        return i18n("已开启局域网分享, 重启WebUI生效")
    else:
        config['settings']['local_link'] = False
        save_configs(config, WEBUI_CONFIG)
        logger.info("Local link is disabled")
        return i18n("已关闭局域网分享, 重启WebUI生效")

def save_auto_clean_cache(flag):
    config = load_configs(WEBUI_CONFIG)
    if flag:
        config['settings']['auto_clean_cache'] = True
        save_configs(config, WEBUI_CONFIG)
        logger.info("Auto clean cache is enabled")
        return i18n("已开启自动清理缓存")
    else:
        config['settings']['auto_clean_cache'] = False
        save_configs(config, WEBUI_CONFIG)
        logger.info("Auto clean cache is disabled")
        return i18n("已关闭自动清理缓存")

def change_debug_mode(flag):
    config = load_configs(WEBUI_CONFIG)
    if flag:
        config['settings']['debug'] = True
        save_configs(config, WEBUI_CONFIG)
        return i18n("已开启调试模式")
    else:
        config['settings']['debug'] = False
        save_configs(config, WEBUI_CONFIG)
        return i18n("已关闭调试模式")

def change_theme(theme):
    config = load_configs(WEBUI_CONFIG)
    config['settings']['theme'] = theme
    save_configs(config, WEBUI_CONFIG)
    logger.info(f"Change theme to: {theme}")
    return i18n("主题已更改, 重启WebUI生效")

def update_rename_model_name(model_type):
    if model_type == "UVR_VR_Models":
        downloaded_model = load_vr_model()
        return gr.Dropdown(label=i18n(key="选择模型"), choices=downloaded_model, interactive=True, scale=4)
    else:
        downloaded_model = load_selected_model(model_type)
        return gr.Dropdown(label=i18n("选择模型"), choices=downloaded_model, interactive=True, scale=4)

def rename_name(model_type, model_name, new_name):
    message = i18n("模型") + model_name + i18n("已重命名为") + new_name
    rename_model_type = gr.Dropdown(label=i18n("选择模型类型"), choices=MODEL_CHOICES, value=None, interactive=True, scale=1)
    rename_model_name = gr.Dropdown(label=i18n("选择模型"), choices=[i18n("请先选择模型类型")], value=i18n("请先选择模型类型"), interactive=True, scale=4)

    if model_type == "" or model_name == "" or new_name == "":
        return "", rename_model_type, rename_model_name

    os.makedirs(os.path.join(UNOFFICIAL_MODEL), exist_ok=True)

    try:
        if model_type == "UVR_VR_Models":
            if not new_name.endswith(".pth"):
                return i18n("新模型名称后缀错误!"), rename_model_type, rename_model_name
            if new_name in load_vr_model():
                return i18n("模型名字已存在! 请重新命名!"), rename_model_type, rename_model_name

            try:
                new_model_map = load_configs(os.path.join(UNOFFICIAL_MODEL, "unofficial_vr_model.json"))
            except FileNotFoundError:
                new_model_map = {}

            model_map = load_configs(VR_MODEL)
            uvr_model_dir = load_configs(WEBUI_CONFIG)['settings']['uvr_model_dir']

            for model in model_map.keys():
                if model == model_name:
                    new_config = model_map[model]
                    new_model_map[new_name] = new_config
                    shutil.copy(os.path.join(uvr_model_dir, model_name), os.path.join(uvr_model_dir, new_name))
                    os.unlink(os.path.join(uvr_model_dir, model_name))
                    save_configs(new_model_map, os.path.join(UNOFFICIAL_MODEL, "unofficial_vr_model.json"))
                    logger.info(f"Rename model: {model_name} to {new_name}")
                    return message, rename_model_type, rename_model_name

            if os.path.isfile(os.path.join(UNOFFICIAL_MODEL, "unofficial_vr_model.json")):
                unofficial_model_map = load_configs(os.path.join(UNOFFICIAL_MODEL, "unofficial_vr_model.json"))

                for model in unofficial_model_map.keys():
                    if model == model_name:
                        new_config = unofficial_model_map[model]
                        new_model_map[new_name] = new_config
                        shutil.copy(os.path.join(uvr_model_dir, model_name), os.path.join(uvr_model_dir, new_name))
                        os.unlink(os.path.join(uvr_model_dir, model_name))
                        save_configs(new_model_map, os.path.join(UNOFFICIAL_MODEL, "unofficial_vr_model.json"))
                        logger.info(f"Rename model: {model_name} to {new_name}")
                        return message, rename_model_type, rename_model_name
            raise FileNotFoundError("Model not found")
        else:
            if not new_name.endswith((".ckpt", ".chpt", ".th")):
                return i18n("新模型名称后缀错误!"), rename_model_type, rename_model_name
            if new_name in load_msst_model():
                return i18n("模型名字已存在! 请重新命名!"), rename_model_type, rename_model_name

            try:
                new_model_map = load_configs(os.path.join(UNOFFICIAL_MODEL, "unofficial_msst_model.json"))
            except FileNotFoundError:
                new_model_map = {"multi_stem_models": [], "single_stem_models": [], "vocal_models": []}

            model_map = load_configs(MSST_MODEL)

            for model in model_map[model_type]:
                if model['name'] == model_name:
                    model['name'] = new_name
                    new_model_map[model_type].append(model)
                    shutil.copy(os.path.join(MODEL_FOLDER, model_type, model_name), os.path.join(MODEL_FOLDER, model_type, new_name))
                    os.unlink(os.path.join(MODEL_FOLDER, model_type, model_name))
                    save_configs(new_model_map, os.path.join(UNOFFICIAL_MODEL, "unofficial_msst_model.json"))
                    logger.info(f"Rename model: {model_name} to {new_name}")
                    return message, rename_model_type, rename_model_name

            if os.path.isfile(os.path.join(UNOFFICIAL_MODEL, "unofficial_msst_model.json")):
                unofficial_model_map = load_configs(os.path.join(UNOFFICIAL_MODEL, "unofficial_msst_model.json"))

                for model in unofficial_model_map[model_type]:
                    if model['name'] == model_name:
                        model['name'] = new_name
                        new_model_map[model_type].append(model)
                        shutil.copy(os.path.join(MODEL_FOLDER, model_type, model_name), os.path.join(MODEL_FOLDER, model_type, new_name))
                        os.unlink(os.path.join(MODEL_FOLDER, model_type, model_name))
                        save_configs(new_model_map, os.path.join(UNOFFICIAL_MODEL, "unofficial_msst_model.json"))
                        logger.info(f"Rename model: {model_name} to {new_name}")
                        return message, rename_model_type, rename_model_name
            raise FileNotFoundError("Model not found")

    except Exception as e:
        logger.error(f"Fail to rename model. Error: {e}\n{traceback.format_exc()}")
        gr.Error(i18n("重命名失败!")) + str(e)