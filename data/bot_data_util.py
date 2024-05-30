from wcferry import WxMsg

from utils.singleton import singleton
from data.model import *
from data.engine import Engine


@singleton
class BotData:
    def __init__(self):
        self.engine = Engine()
        self.chatroom = self.get_chatroom()

    def get_chatroom(self):
        result = {}
        data = self.engine.select(Chatroom)
        for chatroom in data:
            result[chatroom.roomid] = {
                "enable": chatroom.enable,
                "admin": chatroom.admin.split(",") if chatroom.admin else []
            }
        return result

    def add_chatroom(self, roomid: str):
        model = Chatroom(roomid=roomid)
        self.engine.insert(model)
        self.chatroom = self.get_chatroom()

    def update_chatroom(self, roomid: str, enable: bool, admin: list[str]):
        data = self.engine.select(Chatroom, roomid=roomid)[0]
        self.engine.update(
            Chatroom,
            data.id,
            enable=enable,
            admin=",".join(admin)
        )
        self.chatroom = self.get_chatroom()

    def save_msg(self, msg: WxMsg):
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
        )
        self.engine.insert(model)





if __name__ == '__main__':
    a = BotData()
    a.add_chatroom("nnnn")
    a.update_chatroom("nnnn", False, ["aaa","aaad"])
    a = 1
