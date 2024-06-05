import random
import json
import time
import threading

from wcferry import WxMsg

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


class Chengyu:
    def __init__(self, Robot):
        self.all_chengyu = all_chengyu
        self.all_chengyu_answer = all_chengyu_answer

        self.robot = Robot
        self.thread_status = {}
        self.thread_stop = False

    def start(self, msg: WxMsg, is_continue=False):
        if is_continue:
            if not self._stop_thread():
                self.robot.when_game_init(msg.roomid)
                logger.info(f"thread_status:{self.thread_status}\nthread_stop:{self.thread_stop}")
                return self.robot.sendTextMsg("继续开始游戏失败，请重新开始。", msg.roomid)

        status, data = self.get_chengyu()
        if status:
            self.robot.sendTextMsg("【看图猜成语】已开始，请直接输入成语作答，60s后自动结束！", msg.roomid)
            self.robot.chatroom_game[msg.roomid]["game_name"] = "chengyu"
            self.robot.chatroom_game[msg.roomid]["status"] = "True"
            self.robot.chatroom_game[msg.roomid]["data"] = {"answer": data["answer"]}
            self.robot.chatroom_game[msg.roomid].update({"start_time": int(time.time())})
            self.robot.sendImageMsg(data["pic"], msg.roomid)
            t = threading.Thread(target=self._count_down, args=(msg,))
            t.start()
        else:
            return self.robot.sendTextMsg(data, msg.roomid)

    def _count_down(self, msg: WxMsg):
        self.thread_status["_count_down"] = True
        promt = True
        while not self.thread_stop:
            if not self.robot.chatroom_game[msg.roomid]["status"]:
                break
            if (int(time.time()) - self.robot.chatroom_game[msg.roomid]["start_time"]) >= 30 and promt:
                promt = False
                answer = self.robot.chatroom_game[msg.roomid]["data"]["answer"]
                self.robot.sendTextMsg(f"时间过半，提示信息：__{answer[1]}__{answer[3]}", msg.roomid)
            if (int(time.time()) - self.robot.chatroom_game[msg.roomid]["start_time"]) >= 60:
                answer = self.robot.chatroom_game[msg.roomid]["data"]["answer"]
                self.robot.sendTextMsg(f"60s内无正确答案，自动结束！\n正确答案：{answer}", msg.roomid)
                self.robot.when_game_init(msg.roomid)
                return
            else:
                time.sleep(1)
                continue
        self.thread_status["_count_down"] = False

    def _stop_thread(self):
        self.thread_stop = True
        for _ in range(5):
            if self.thread_status["_count_down"]:
                time.sleep(0.5)
                continue
            else:
                self.thread_stop = False
                return True
        return False

    def process(self, msg: WxMsg):
        if msg.content == self.robot.chatroom_game[msg.roomid]["data"]["answer"]:
            status, data = self.chengyu_answer(msg.content)
            name = self.robot.wcf.get_alias_in_chatroom(msg.sender, msg.roomid)
            resp = f"🎉🎉恭喜【{name}】答对🎉🎉"
            if status:
                explain = data
            else:
                explain = ""
            self.robot.sendTextMsg(resp + explain, msg.roomid)
            game_data = self.robot.bot_data.get_game_chengyu(roomid=msg.roomid, wxid=msg.sender)
            if not game_data:
                self.robot.bot_data.add_game_chengyu(msg.roomid, msg.sender)
            else:
                self.robot.bot_data.update_game_chengyu(msg.roomid, msg.sender, score=game_data.score + 1)
            all_game_data = self.robot.bot_data.get_game_chengyu(all_data=True, roomid=msg.roomid)
            resp = "[排名][得分][昵称]"
            for i in range(len(all_game_data) if len(all_game_data) <= 10 else 10):
                name = self.robot.wcf.get_alias_in_chatroom(all_game_data[i].wxid, all_game_data[i].roomid)
                resp += f"\n{i + 1}.💯[{all_game_data[i].score}]👉{name}"
            self.robot.sendTextMsg(resp, msg.roomid)

            self.start(msg, is_continue=True)
            return
        else:
            return

    def get_chengyu(self):
        try:
            file_name = f"{random.randint(1, 475):03d}"
            answer = self.all_chengyu[file_name]["text"]
            return True, {"answer": answer, "pic": str(DEFAULT_PATH / "Bot" / "plugins" / "data" / "chengyu" / f"{file_name}.png")}
        except Exception as e:
            logger.error(str(e))
            return False, "[看图猜成语]插件出现故障，请联系开发者"

    def chengyu_answer(self, text):
        try:
            data = self.all_chengyu_answer[text]
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


