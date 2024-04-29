import requests

from utils.log import logger_manager

logger = logger_manager.logger


def shadiao(type):
    if type == "疯狂星期四":
        url = "https://api.shadiao.pro/kfc"
        error_msg = "疯狂星期四插件出现故障，请联系开发者"
    elif type == "彩虹屁":
        url = "https://api.shadiao.pro/chp"
        error_msg = "彩虹屁插件出现故障，请联系开发者"
    elif type == "朋友圈" or type == "朋友圈文案":
        url = "https://api.shadiao.pro/pyq"
        error_msg = "朋友圈文案插件出现故障，请联系开发者"
    else:
        assert False, 'type error'
    try:
        resp = requests.get(url)
        return resp.json()["data"]["text"]
    except Exception as e:
        logger.error(str(e))
        return error_msg



if __name__ == '__main__':
    shadiao("彩虹屁")

