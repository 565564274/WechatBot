import random
import json

from utils.log import logger_manager
from utils.root_path import DEFAULT_PATH

logger = logger_manager.logger


# all files from https://qm2u.com/chengyu/
all_chengyu_jsonl_path = DEFAULT_PATH / "Bot" / "plugins" / "data" / "all_chengyu.jsonl"
all_chengyu = {}
all_chengyu_answer = {}

with open(all_chengyu_jsonl_path, 'r', encoding='utf-8') as infile:
    for line in infile:
        # 解析每一行的JSON对象
        json_obj = json.loads(line)
        all_chengyu.update(json_obj)
        for key, value in json_obj.items():
            all_chengyu_answer[value["text"]] = value["data"]


def chengyu():
    try:
        file_name = f"{random.randint(1, 475):03d}"
        answer = all_chengyu[file_name]["text"]
        return True, {"answer": answer, "pic": str(DEFAULT_PATH / "Bot" / "plugins" / "data" / "chengyu" / f"{file_name}.png")}
    except Exception as e:
        logger.error(str(e))
        return False, "[看图猜成语]插件出现故障，请联系开发者"


def chengyu_answer(text):
    try:
        data = all_chengyu_answer[text]
        if data["code"] == "1":
            explain = (f'\n'
                       f'【答案】{data["cycx"].split("-")[0]}\n'
                       f'【拼音】{data["cycx"].split("-")[1]}\n'
                       f'【解释】{data["cyjs"]}\n'
                       f'【出处】{data["cycc"]}\n'
                       f'【造句】{data["cyzj"]}\n')
        else:
            explain = ""
        return True, explain
    except Exception as e:
        logger.error(str(e))
        return False, "[看图猜成语]插件出现故障，请联系开发者"


# def chengyu():
#     url = f"https://xiaoapi.cn/API/game_ktccy.php?msg=开始游戏&id={int(time.time())}"
#     error_msg = "[看图猜成语]插件出现故障，请联系开发者"
#     try:
#         resp = requests.get(url)
#         if resp.status_code != 200:
#             assert False, "response code is not 200"
#         return True, {"answer": resp.json()["data"]["answer"], "pic": resp.json()["data"]["pic"]}
#     except Exception as e:
#         logger.error(str(e))
#         return False, error_msg
#
#
# def chengyu_answer(text):
#     url = f"https://v.api.aa1.cn/api/api-chengyu/index.php?msg={text}"
#     error_msg = "[看图猜成语]插件出现故障，请联系开发者"
#     try:
#         resp = requests.get(url, timeout=3)
#         if resp.status_code != 200:
#             assert False, "response code is not 200"
#         return True, resp.json()
#     except Exception as e:
#         logger.error(str(e))
#         return False, error_msg


