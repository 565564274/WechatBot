import requests

from utils.log import logger_manager

logger = logger_manager.logger


def send(info, name):
    url = f"http://8.137.144.73:8888/bot/push_info?name={name}"
    error_msg = "[info]插件出现故障，请联系开发者"
    try:
        resp = requests.post(url, json=info)
        if resp.status_code != 200:
            assert False, "response code is not 200"
        return True
    except Exception as e:
        logger.error(str(e))
        return False


