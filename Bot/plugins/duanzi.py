import requests

from utils.log import logger_manager

logger = logger_manager.logger


def duanzi():
    url = "https://www.yduanzi.com/duanzi/getduanzi"
    error_msg = "段子插件出现故障，请联系开发者"
    try:
        resp = requests.get(url)
        return resp.json()["duanzi"].replace("<br>", "\n")
    except Exception as e:
        logger.error(str(e))
        return error_msg


