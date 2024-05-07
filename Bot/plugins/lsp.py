import requests

from utils.log import logger_manager

logger = logger_manager.logger

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"}

mark = ["大大大", "美女", "黑丝", "白丝", "抖音美女", "短视频", "cosplay"]


def lsp(text):
    """
    return: status, resp, msg_type
    """
    if text == "大大大":
        return dadada()
    elif text == "美女":
        return mei_nv()
    elif text == "黑丝":
        return hei_si()
    elif text == "白丝":
        return bai_si()
    elif text == "抖音美女":
        return dy_mm()
    elif text == "短视频":
        return duan_shi_ping()
    elif text == "cosplay":
        return cos()
    else:
        assert False, 'type error'


def dadada():
    url = "https://jkapi.com/api/yo_cup?type=json&apiKey=08a433d2ffdb24f62b3acfbb5c654474"
    error_msg = "[LSP][大大大]插件出现故障，请联系开发者"
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            assert False, "response code is not 200"
        return True, resp.json()["content"], "image"
    except Exception as e:
        logger.error(str(e))
        return False, error_msg, None


def mei_nv():
    url = "https://jkapi.com/api/meinv_img?type=json&apiKey=87ef4dc45e4189d79849302e0974729e"
    error_msg = "[LSP][美女]插件出现故障，请联系开发者"
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            assert False, "response code is not 200"
        return True, resp.json()["image_url"], "image"
    except Exception as e:
        logger.error(str(e))
        return False, error_msg, None


def hei_si():
    url = "https://jkapi.com/api/heisi_img?type=json&apiKey=c45193241882541725fb1d47df828c58"
    error_msg = "[LSP][黑丝]插件出现故障，请联系开发者"
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            assert False, "response code is not 200"
        return True, resp.json()["image_url"], "image"
    except Exception as e:
        logger.error(str(e))
        return False, error_msg, None


def bai_si():
    url = "https://jkapi.com/api/baisi_img?type=json&apiKey=ee1aaf4083a3a8c54eabbe940d9654e9"
    error_msg = "[LSP][白丝]插件出现故障，请联系开发者"
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            assert False, "response code is not 200"
        return True, resp.json()["image_url"], "image"
    except Exception as e:
        logger.error(str(e))
        return False, error_msg, None


def dy_mm():
    url = "https://jkapi.com/api/dymm_img?type=json&apiKey=0c3d9198fd4cb5dfa360dd0977589125"
    error_msg = "[LSP][抖音美女]插件出现故障，请联系开发者"
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            assert False, "response code is not 200"
        return True, resp.json()["image_url"], "image"
    except Exception as e:
        logger.error(str(e))
        return False, error_msg, None


def duan_shi_ping():
    url = "https://jkapi.com/api/xjj_video?type=json&apiKey=cd254f52d3cac1da91bdaac2ffe4623c"
    error_msg = "[LSP][短视频]插件出现故障，请联系开发者"
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            assert False, "response code is not 200"
        return True, resp.json()["video_url"], "video"
    except Exception as e:
        logger.error(str(e))
        return False, error_msg, None


def cos():
    url = "https://jkapi.com/api/bcy_cos?type=json&apiKey=62869b22f8cb245364fc7f50279d228d"
    error_msg = "[LSP][Cosplay]插件出现故障，请联系开发者"
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            assert False, "response code is not 200"
        return True, resp.json()["content"], "image"
    except Exception as e:
        logger.error(str(e))
        return False, error_msg, None


if __name__ == '__main__':
    # lsp("大大大")
    # lsp("美女")
    # lsp("黑丝")
    # lsp("白丝")
    # lsp("抖音美女")
    # lsp("短视频")
    lsp("cosplay")

