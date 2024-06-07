import time
import threading
import requests

from wcferry import WxMsg

from utils.log import logger_manager

logger = logger_manager.logger


class Caige:
    def __init__(self, Robot):
        self.robot = Robot
        self.thread_status = {}
        self.thread_stop = False
        self.explain = ""

    def start(self, msg: WxMsg, is_continue=False):
        if is_continue:
            if not self._stop_thread():
                self.robot.when_game_init(msg.roomid)
                logger.info(f"thread_status:{self.thread_status}\nthread_stop:{self.thread_stop}")
                return self.robot.sendTextMsg("继续开始游戏失败，请重新开始。", msg.roomid)

        status, data = self.get_music()
        if status:
            self.robot.sendTextMsg("【猜歌】已开始，请直接输入歌名作答，60s后自动结束！", msg.roomid)
            self.robot.chatroom_game[msg.roomid]["game_name"] = "caige"
            self.robot.chatroom_game[msg.roomid]["status"] = True
            self.robot.chatroom_game[msg.roomid]["data"] = {"answer": data["name"]}
            self.robot.chatroom_game[msg.roomid].update({"start_time": int(time.time())})
            self.robot.wcf.send_rich_text(
                name="",
                account="",
                title="🎶🎶请听歌曲，并作答🎶🎶",
                digest=f"",
                url=data["url"],
                thumburl=data["picurl"],
                receiver=msg.roomid
            )
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
                self.robot.sendTextMsg(f"时间过半，提示信息：{answer[0]}{' __ ' * (len(answer) - 1)}", msg.roomid)
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
            name = self.robot.wcf.get_alias_in_chatroom(msg.sender, msg.roomid)
            resp = f"🎉🎉恭喜【{name}】答对🎉🎉"
            self.robot.sendTextMsg(resp + self.explain, msg.roomid)
            game_data = self.robot.bot_data.get_game_caige(roomid=msg.roomid, wxid=msg.sender)
            if not game_data:
                self.robot.bot_data.add_game_caige(msg.roomid, msg.sender)
            else:
                self.robot.bot_data.update_game_caige(msg.roomid, msg.sender, score=game_data.score + 1)
            all_game_data = self.robot.bot_data.get_game_caige_score(roomid=msg.roomid)
            resp = "[排名][得分][昵称]"
            for i in range(len(all_game_data)):
                if i == 0:
                    icon = "🥇"
                elif i == 1:
                    icon = "🥈"
                elif i == 2:
                    icon = "🥉"
                else:
                    icon = "💯"
                name = self.robot.wcf.get_alias_in_chatroom(all_game_data[i].wxid, all_game_data[i].roomid)
                resp += f"\n{i + 1}.{icon}[{all_game_data[i].score}]👉{name}"
            self.robot.sendTextMsg(resp, msg.roomid)

            self.start(msg, is_continue=True)
            return
        else:
            return

    def get_music(self):
        url = f"https://free.wqwlkj.cn/wqwlapi/wyy_random.php"
        error_msg = "[猜歌]插件出现故障，请联系开发者"
        try:
            resp = requests.get(url)
            logger.info(str(resp.json()))
            if resp.status_code != 200:
                assert False, "response code is not 200"
            if resp.json()["code"] != 1:
                assert False, "resp.json()[\"code\"] code is not 200"
            data = resp.json()["data"]
            self.explain = (f'\n'
                            f'【歌名】{data["name"]}\n'
                            f'【演唱】{data["artistsname"]}\n'
                            f'【专辑】{data["alname"]}\n')
            return True, data
        except Exception as e:
            logger.error(str(e))
            return False, error_msg


