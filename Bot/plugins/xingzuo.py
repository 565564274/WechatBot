import time

import requests

from utils.log import logger_manager
from utils.root_path import DEFAULT_TEMP_PATH

logger = logger_manager.logger


mark = [
    "白羊座",  # Aries
    "金牛座",  # Taurus
    "双子座",  # Gemini
    "巨蟹座",  # Cancer
    "狮子座",  # Leo
    "处女座",  # Virgo
    "天秤座",  # Libra
    "天蝎座",  # Scorpio
    "射手座",  # Sagittarius
    "摩羯座",  # Capricorn
    "水瓶座",  # Aquarius
    "双鱼座"   # Pisces
]


def xingzuo(text):
    url = f"https://xiaoapi.cn/API/xzys_pic.php?msg={text}"
    error_msg = "[星座运势]插件出现故障，请联系开发者"
    try:
        resp = requests.get(url)
        if resp.status_code != 200:
            assert False, "response code is not 200"
        if resp.headers['Content-Type'] != 'image/jpeg':
            assert False, "headers is not image/jpeg"
        path = DEFAULT_TEMP_PATH / f"{int(time.time())}.jpg"
        with open(path, 'wb') as file:
            file.write(resp.content)
        return True, path
    except Exception as e:
        logger.error(str(e))
        return False, error_msg

xingzuo("狮子座")
