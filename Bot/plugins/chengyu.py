import requests
import time

from utils.log import logger_manager

logger = logger_manager.logger


def chengyu():
    url = f"https://xiaoapi.cn/API/game_ktccy.php?msg=开始游戏&id={int(time.time())}"
    error_msg = "[看图猜成语]插件出现故障，请联系开发者"
    try:
        resp = requests.get(url)
        if resp.status_code != 200:
            assert False, "response code is not 200"
        return True, {"answer": resp.json()["data"]["answer"], "pic": resp.json()["data"]["pic"]}
    except Exception as e:
        logger.error(str(e))
        return False, error_msg


def chengyu_answer(text):
    url = f"https://v.api.aa1.cn/api/api-chengyu/index.php?msg={text}"
    error_msg = "[看图猜成语]插件出现故障，请联系开发者"
    try:
        resp = requests.get(url, timeout=3)
        if resp.status_code != 200:
            assert False, "response code is not 200"
        return True, resp.json()
    except Exception as e:
        logger.error(str(e))
        return False, error_msg

if __name__ == '__main__':
    chengyu_answer("一言不合")
