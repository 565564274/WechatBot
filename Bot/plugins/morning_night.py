import requests

from utils.log import logger_manager

logger = logger_manager.logger

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"}


def zao_an():
    url = "https://jkapi.com/api/zaoan?type=json"
    error_msg = "[早安]插件出现故障，请联系开发者"
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            assert False, "response code is not 200"
        return resp.json()["content"]
    except Exception as e:
        logger.error(str(e))
        return error_msg


def wan_an():
    url = "https://jkapi.com/api/wanan?type=json"
    error_msg = "[晚安]插件出现故障，请联系开发者"
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            assert False, "response code is not 200"
        return resp.json()["content"]
    except Exception as e:
        logger.error(str(e))
        return error_msg


