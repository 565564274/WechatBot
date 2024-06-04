import threading

from wcferry import WxMsg

from utils.singleton import singleton
from data.model import *
from data.engine import Engine


@singleton
class BotData:
    def __init__(self):
        self.engine = Engine()
        self.lock = {
            "Chatroom": threading.Lock(),
            "ChatroomBan": threading.Lock(),
            "MsgHistory": threading.Lock(),
            "GameChengyu": threading.Lock(),
            "GameXiuxian": threading.Lock(),
        }

        self.chatroom = self.get_chatroom()

    def get_chatroom(self):
        result = {}
        data = self.engine.select(Chatroom)
        for chatroom in data:
            result[chatroom.roomid] = {
                "enable": chatroom.enable,
                "admin": chatroom.admin.split(",") if chatroom.admin else [],
                "ban_keywords": chatroom.ban_keywords.split("|") if chatroom.ban_keywords else [],
                "status_avoid_revoke": chatroom.status_avoid_revoke,
                "status_ban_keywords": chatroom.status_ban_keywords,
                "status_inout_monitor": chatroom.status_inout_monitor,
            }
        return result

    def add_chatroom(self, roomid: str):
        with self.lock["Chatroom"]:
            model = Chatroom(roomid=roomid)
            self.engine.insert(model)
            self.chatroom = self.get_chatroom()

    def update_chatroom(self, roomid: str, **kwargs):
        with self.lock["Chatroom"]:
            data = self.engine.select(Chatroom, roomid=roomid)[0]
            self.engine.update(
                Chatroom,
                data.id,
                **kwargs
            )
            self.chatroom = self.get_chatroom()

    def get_msg(self, roomid: str, msg_id: str):
        data = self.engine.select(MsgHistory, roomid=roomid, msg_id=msg_id)
        if data:
            return data[0]
        return data

    def add_msg(self, msg: WxMsg, path: str = None):
        with self.lock["MsgHistory"]:
            model = MsgHistory(
                sender=msg.sender,
                roomid=msg.roomid,
                msg_id=msg.id,
                ts=msg.ts,
                type=msg.type,
                xml=msg.xml,
                content=msg.content,
                thumb=msg.thumb,
                extra=msg.extra,
                path=path
            )
            self.engine.insert(model)

    def get_ban(self, roomid: str, wxid: str):
        data = self.engine.select(ChatroomBan, roomid=roomid, wxid=wxid)
        if data:
            return data[0]
        return data

    def add_ban(self, roomid: str, wxid: str):
        with self.lock["ChatroomBan"]:
            model = ChatroomBan(
                roomid=roomid,
                wxid=wxid,
            )
            self.engine.insert(model)

    def update_ban(self, roomid: str, wxid: str, **kwargs):
        with self.lock["ChatroomBan"]:
            data = self.engine.select(ChatroomBan, roomid=roomid, wxid=wxid)[0]
            self.engine.update(
                ChatroomBan,
                data.id,
                **kwargs
            )

    def get_game_chengyu(self, all_data=False, **kwargs):
        data = self.engine.select(GameChengyu, **kwargs)
        if data:
            if all_data:
                return data
            return data[0]
        return data

    def add_game_chengyu(self, roomid: str, wxid: str):
        with self.lock["GameChengyu"]:
            model = GameChengyu(
                roomid=roomid,
                wxid=wxid,
            )
            self.engine.insert(model)

    def update_game_chengyu(self, roomid: str, wxid: str, **kwargs):
        with self.lock["GameChengyu"]:
            data = self.engine.select(GameChengyu, roomid=roomid, wxid=wxid)[0]
            self.engine.update(
                GameChengyu,
                data.id,
                **kwargs
            )

    def get_game_xiuxian(self, all_data=False, **kwargs):
        data = self.engine.select(GameXiuxian, **kwargs)
        if data:
            if all_data:
                return data
            return data[0]
        return data

    def add_game_xiuxian(self, roomid: str, wxid: str):
        with self.lock["GameXiuxian"]:
            model = GameXiuxian(
                roomid=roomid,
                wxid=wxid,
            )
            self.engine.insert(model)

    def update_game_xiuxian(self, roomid: str, wxid: str, **kwargs):
        with self.lock["GameXiuxian"]:
            data = self.engine.select(GameXiuxian, roomid=roomid, wxid=wxid)[0]
            result = self.engine.update(
                GameXiuxian,
                data.id,
                **kwargs
            )
            return result


if __name__ == '__main__':
    a = BotData()
    a.get_chatroom()
    a.update_chatroom(
        "20782264501@chatroom", False, ["aaa","aaad"],
        status_avoid_revoke=True,
        status_ban_keywords=True,
        status_inout_monitor=False,
    )
    a = 1
