import requests

from utils.log import logger_manager

logger = logger_manager.logger


def zhanan_lvcha(type):
    url = (f"https://api.lovelive.tools/api/SweetNothings/1/Serialization/Json?genderType="
           f"{'M' if type == '渣男' else 'F'}")
    error_msg = "渣男&绿茶插件出现故障，请联系开发者"
    try:
        resp = requests.get(url)
        return resp.json()["returnObj"][0]
    except Exception as e:
        logger.error(str(e))
        return error_msg


