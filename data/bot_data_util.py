from utils.singleton import singleton
from data.model import *
from data.engine import Engine


@singleton
class BotData:
    def __init__(self):
        self.engine = Engine()
        self.chatroom = self.get_chatroom()

    def get_chatroom(self):
        result = []
        data = self.engine.select(Chatroom)
        for chatroom in data:
            if chatroom.enable:
                result.append(chatroom)
        return result

    def add_chatroom(self, roomid: str):
        model = Chatroom(
            roomid=roomid
        )
        self.engine.insert(model)

    def update_chatroom(self):
        self.engine.update(
            Chatroom,
            1,
            enable=True
        )





if __name__ == '__main__':
    a = BotData()
    a.add_chatroom("nnnn")
















