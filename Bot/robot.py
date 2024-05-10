import re
import time
import xml.etree.ElementTree as ET
import threading

from wcferry import Wcf, WxMsg
from queue import Empty
from threading import Thread
from datetime import datetime, timedelta
from pathlib import Path

from utils.log import logger_manager
from utils.singleton import singleton

from Bot.job_mgmt import Job
from Bot.plugins.pokeme import pokeme_reply
from Bot.plugins.qingganyulu import get_yulu
from Bot.plugins.shadiao import shadiao
from Bot.plugins.zhanan_lvcha import zhanan_lvcha
from Bot.plugins.duanzi import duanzi
from Bot.plugins.news import News
from Bot.plugins import lsp
from Bot.plugins import morning_night
from Bot.plugins import info
from Bot.plugins.chatgpt import ChatgptApi
from utils.root_path import DEFAULT_TEMP_PATH


def new_str(self) -> str:
    s = "=" * 32 * 6 + "\n"
    s += f"{'自己发的:' if self._is_self else ''}"
    s += f"{self.sender}[{self.roomid}]|{self.id}|{datetime.fromtimestamp(self.ts)}|{self.type}|{self.sign}"
    s += f"\n{self.xml.replace(chr(10), '').replace(chr(9), '')}"
    s += f"\ncontent: {self.content}"
    s += f"\nthumb: {self.thumb}" if self.thumb else ""
    s += f"\nextra: {self.extra}" if self.extra else ""
    return s


WxMsg.__str__ = new_str


@singleton
class Robot(Job):

    def __init__(self, config, wcf: Wcf) -> None:
        self.wcf = wcf
        self.config = config
        self.LOG = logger_manager.logger
        self.wxid = self.wcf.get_self_wxid()
        self.allContacts = self.getAllContacts()
        self.chatgpt = ChatgptApi()
        self.all_user = self.config.USER if self.config.USER else {}
        self.all_user_lock = {}
        for key in self.all_user.keys():
            self.all_user_lock[key] = threading.Lock()
        self.VOICE, error = self.config.read_excel()

    def processMsg(self, msg: WxMsg) -> None:
        """当接收到消息的时候，会调用本方法。如果不实现本方法，则打印原始消息。
        此处可进行自定义发送的内容,如通过 msg.content 关键字自动获取当前天气信息，并发送到对应的群组@发送者
        群号：msg.roomid  微信ID：msg.sender  消息内容：msg.content
        content = "xx天气信息为："
        receivers = msg.roomid
        self.sendTextMsg(content, receivers, msg.sender)
        """

        # 群聊消息
        if msg.from_group():
            return  # 处理完群聊信息，后面就不需要处理了

        # 初始化
        if msg.sender not in self.all_user:
            self.all_user[msg.sender] = {
                "conversation": [],
                "voice": False,
                "voice_scene": None,
                "certification": False,
                "free": 10
            }
            self.all_user_lock[msg.sender] = threading.Lock()

        # 非群聊信息，按消息类型进行处理
        if msg.type == 37:  # 好友请求
            self.autoAcceptFriendRequest(msg)

        elif msg.type == 10000:  # 系统信息
            self.sayHiToNewFriend(msg)

        elif msg.type == 1:  # 文本消息
            # 让配置加载更灵活，自己可以更新配置。也可以利用定时任务更新。
            if msg.from_self():
                return
            if msg.content.startswith("@") and msg.sender in self.config.ADMIN:
                return self.admin(msg)

            if not self.check_cert(msg.sender):
                self.sendTextMsg("无免费额度/激活已过期，请咨询客服", msg.sender)
                return
            if msg.content == "结束对话":
                self.all_user[msg.sender]["conversation"] = []
                self.all_user[msg.sender]["voice"] = False
                self.all_user[msg.sender]["voice_scene"] = None
                self.sendTextMsg("对话已结束", msg.sender)
                return
            if self.all_user[msg.sender]["voice"]:
                self.sendTextMsg("处于对话场景中，无法文字对话，请输入【结束对话】退出场景。", msg.sender)
                return
            if msg.content == "查看场景":
                resp = "场景如下：\n"
                for i, info in self.VOICE.items():
                    resp += f"【{i}】 {info['name']}\n"
                    if i >= 5:
                        break
                resp += "......\n更多场景请咨询客服获取\n"
                self.sendTextMsg(resp + "请输入#+场景编号进入场景对话\n如#1", msg.sender)
                return
            elif msg.content.startswith("#"):
                if msg.content[1:] in [str(key) for key in self.VOICE.keys()]:
                    self.sendTextMsg(f'已选择【{self.VOICE[int(msg.content[1:])]["name"]}】场景，请开始发送语音', msg.sender)
                    self.all_user[msg.sender]["voice"] = True
                    self.all_user[msg.sender]["voice_scene"] = self.VOICE[int(msg.content[1:])]["description"]
                    return
                else:
                    self.sendTextMsg("无效场景，请重新输入", msg.sender)
                    return
            elif msg.content == "查看激活":
                if self.all_user[msg.sender]["certification"]:
                    self.sendTextMsg(f'激活到期时间：{self.all_user[msg.sender]["certification"]}', msg.sender)
                else:
                    if self.all_user[msg.sender]["free"] > 0:
                        self.sendTextMsg(f'还未激活，免费额度剩余：{self.all_user[msg.sender]["free"]}', msg.sender)
                    else:
                        self.sendTextMsg(f'还未激活，免费额度已用完', msg.sender)
                return
            elif msg.content == "获取账户":
                self.sendTextMsg(msg.sender, msg.sender)
                return
            else:
                resp = ("输入【查看场景】并根据教程选择场景对话\n"
                        "输入【结束对话】结束当前场景对话\n"
                        "输入【获取账户】获取账户名咨询客服激活\n"
                        "输入【查看激活】查看激活到期时间\n"
                        "初始拥有10条免费语音对话次数")
                self.sendTextMsg(resp, msg.sender)
                return
        elif msg.type == 34:  # 语音消息
            if msg.from_self():
                return
            if not self.all_user[msg.sender]["voice"]:
                self.sendTextMsg("还未选择对话场景，无法语音对话，请输入【帮助】查看使用教程。", msg.sender)
                return
            if not self.check_cert(msg.sender):
                self.sendTextMsg("无免费额度/激活已过期，请咨询客服", msg.sender)
                return
            t = threading.Thread(target=self.reply, args=(msg,))
            t.start()

    def check_cert(self, wx_id):
        if self.all_user[wx_id]["free"] > 0:
            self.all_user[wx_id]["free"] -= 1
            return True
        if self.all_user[wx_id]["certification"]:
            certification = datetime.strptime(self.all_user[wx_id]["certification"], "%Y-%m-%d %H:%M:%S")
            if certification > datetime.now():
                return True
        self.all_user[wx_id]["conversation"] = []
        self.all_user[wx_id]["voice"] = False
        self.all_user[wx_id]["voice_scene"] = None
        return False

    def reply(self, msg: WxMsg):
        with self.all_user_lock[msg.sender]:
            self.LOG.info("*" * 32 * 6 + "\n")
            self.LOG.info(f"处理{msg.sender}语音")
            wx_id_receive_folder = DEFAULT_TEMP_PATH / msg.sender
            if not Path(wx_id_receive_folder).is_dir():
                Path(wx_id_receive_folder).mkdir(exist_ok=True)
            receive_path = self.wcf.get_audio_msg(msg.id, str(wx_id_receive_folder), timeout=30)
            if not receive_path:
                return self.sendTextMsg("请重新发送语音，识别异常", msg.sender)
            status, transcription = self.chatgpt.whisper(Path(receive_path))
            if not status:
                return self.sendTextMsg("请重新发送语音，识别异常", msg.sender)
            self.all_user[msg.sender]["conversation"].append(["user", transcription])
            self.LOG.info(self.all_user[msg.sender]["conversation"])
            status, resp = self.chatgpt.chat(
                self.all_user[msg.sender]["conversation"],
                role=self.all_user[msg.sender]["voice_scene"]
            )
            if not status:
                return self.sendTextMsg("请重新发送语音，回复异常", msg.sender)
            status, output_path = self.chatgpt.tts(resp, msg.sender)
            if not status:
                return self.sendTextMsg("请重新发送语音，回复异常", msg.sender)
            self.sendTextMsg(f"{resp}\n————————————\n点击下方⬇️文件听语音", msg.sender)
            status = self.sendFileMsg(str(output_path), msg.sender)
            if not status:
                return self.sendTextMsg("请重新发送语音，发送异常", msg.sender)
            self.all_user[msg.sender]["conversation"].append(["assistant", resp])
            self.LOG.info(resp)
            self.LOG.info("*" * 32 * 6 + "\n")

    def admin(self, msg: WxMsg) -> None:
        """
        处理administrators(创建者)的@消息
        :param msg: 微信消息结构
        :return: 处理状态，`True` 成功，`False` 失败
        """
        if msg.content.startswith("@帮助"):
            self.sendTextMsg(
                "指令如下：\n"
                "以当前时间为起点增加X天↓\n"
                "@增加激活 {账户名} {增加天数}\n"
                "以到期时间为起点减少X天↓\n"
                "@减少激活 {账户名} {减少天数}\n"
                "查询到期时间↓\n"
                "@查询激活 {账户名}\n"
                "更新对话场景↓\n"
                "@更新场景\n",
                msg.sender)
        elif msg.content.startswith("@增加激活"):
            order = msg.content.split(" ")
            if not order[1] in self.all_user:
                self.sendTextMsg("未查询到此账户", msg.sender)
            else:
                end_time = datetime.now() + timedelta(days=int(order[2]))
                end_time_str = datetime.strftime(end_time, "%Y-%m-%d %H:%M:%S")
                self.all_user[msg.sender]["certification"] = end_time_str
                self.config.resource["user"] = self.all_user
                self.config.rewrite_reload()
                self.sendTextMsg(f'增加成功\n账户：{msg.sender}\n过期时间：{end_time_str}', msg.sender)
        elif msg.content.startswith("@减少激活"):
            order = msg.content.split(" ")
            if not order[1] in self.all_user:
                self.sendTextMsg("未查询到此账户", msg.sender)
            else:
                end_time = datetime.now() - timedelta(days=int(order[2]))
                end_time_str = datetime.strftime(end_time, "%Y-%m-%d %H:%M:%S")
                self.all_user[msg.sender]["certification"] = end_time_str
                self.config.resource["user"] = self.all_user
                self.config.rewrite_reload()
                self.sendTextMsg(f'减少成功\n账户：{msg.sender}\n过期时间：{end_time_str}', msg.sender)
        elif msg.content.startswith("@查询激活"):
            order = msg.content.split(" ")
            if not order[1] in self.all_user:
                self.sendTextMsg("未查询到此账户", msg.sender)
            else:
                self.sendTextMsg(f'账户：{msg.sender}\n过期时间：{self.all_user[msg.sender]["certification"]}', msg.sender)
        elif msg.content.startswith("@更新场景"):
            self.VOICE, error = self.config.read_excel()
            self.sendTextMsg(f'更新成功：{len(self.VOICE)}行\n'
                             f'{"" if not error else f"更新失败：表中{error}行"}',
                             msg.sender)
        else:
            self.sendTextMsg("未识别指令", msg.roomid, msg.sender)

    def toAt(self, msg: WxMsg) -> bool:
        """处理被 @ 消息
        :param msg: 微信消息结构
        :return: 处理状态，`True` 成功，`False` 失败
        """
        return self.toChitchat(msg)

    def toChengyu(self, msg: WxMsg) -> bool:
        """
        处理成语查询/接龙消息
        :param msg: 微信消息结构
        :return: 处理状态，`True` 成功，`False` 失败
        """
        status = False
        texts = re.findall(r"^([#|?|？])(.*)$", msg.content)
        # [('#', '天天向上')]
        if texts:
            flag = texts[0][0]
            text = texts[0][1]
            if flag == "#":  # 接龙
                if cy.isChengyu(text):
                    rsp = cy.getNext(text)
                    if rsp:
                        self.sendTextMsg(rsp, msg.roomid)
                        status = True
            elif flag in ["?", "？"]:  # 查词
                if cy.isChengyu(text):
                    rsp = cy.getMeaning(text)
                    if rsp:
                        self.sendTextMsg(rsp, msg.roomid)
                        status = True

        return status

    def toChitchat(self, msg: WxMsg) -> bool:
        """闲聊，接入 ChatGPT
        """
        if not self.chat:  # 没接 ChatGPT，固定回复
            rsp = "你@我干嘛？"
        else:  # 接了 ChatGPT，智能回复
            q = re.sub(r"@.*?[\u2005|\s]", "", msg.content).replace(" ", "")
            rsp = self.chat.get_answer(q, (msg.roomid if msg.from_group() else msg.sender))

        if rsp:
            if msg.from_group():
                self.sendTextMsg(rsp, msg.roomid, msg.sender)
            else:
                self.sendTextMsg(rsp, msg.sender)

            return True
        else:
            self.LOG.error(f"无法从 ChatGPT 获得答案")
            return False

    def enableReceivingMsg(self) -> None:
        def innerProcessMsg(wcf: Wcf):
            while wcf.is_receiving_msg():
                try:
                    msg = wcf.get_msg()
                    self.LOG.info(msg)
                    self.processMsg(msg)
                except Empty:
                    continue  # Empty message
                except Exception as e:
                    self.LOG.error(f"Receiving message error: {e}")

        self.wcf.enable_receiving_msg()
        Thread(target=innerProcessMsg, name="GetMessage", args=(self.wcf,), daemon=True).start()

    def sendTextMsg(self, msg: str, receiver: str, at_list: str = "") -> None:
        """ 发送消息
        :param msg: 消息字符串
        :param receiver: 接收人wxid或者群id
        :param at_list: 要@的wxid, @所有人的wxid为：notify@all
        """
        # msg 中需要有 @ 名单中一样数量的 @
        ats = ""
        if at_list:
            if at_list == "notify@all":  # @所有人
                ats = " @所有人"
            else:
                wxids = at_list.split(",")
                for wxid in wxids:
                    # 根据 wxid 查找群昵称
                    ats += f" @{self.wcf.get_alias_in_chatroom(wxid, receiver)}"

        # {msg}{ats} 表示要发送的消息内容后面紧跟@，例如 北京天气情况为：xxx @张三
        if ats == "":
            self.LOG.info(f"To {receiver}: {msg}")
            self.wcf.send_text(f"{msg}", receiver, at_list)
        else:
            self.LOG.info(f"To {receiver}: {ats}\r{msg}")
            self.wcf.send_text(f"{ats}\n\n{msg}", receiver, at_list)

    def sendImageMsg(self, image_path: str, receiver: str) -> None:
        """ 发送消息
        :param image_path:
        :param receiver: 接收人wxid或者群id
        """
        self.LOG.info(f"To {receiver}: {image_path}")
        status = self.wcf.send_image(image_path, receiver)
        if status != 0:
            self.sendTextMsg("发送图片失败", receiver)

    def sendFileMsg(self, file_path: str, receiver: str) -> bool:
        """ 发送消息
        :param file_path:
        :param receiver: 接收人wxid或者群id
        """
        self.LOG.info(f"To {receiver}: {file_path}")
        status = self.wcf.send_file(file_path, receiver)
        if status != 0:
            return False
        else:
            return True

    def getAllContacts(self) -> dict:
        """
        获取联系人（包括好友、公众号、服务号、群成员……）
        格式: {"wxid": "NickName"}
        """
        contacts = self.wcf.query_sql("MicroMsg.db", "SELECT UserName, NickName FROM Contact;")
        return {contact["UserName"]: contact["NickName"] for contact in contacts}

    def keepRunningAndBlockProcess(self) -> None:
        """
        保持机器人运行，不让进程退出
        """
        while True:
            self.runPendingJobs()
            time.sleep(1)

    def autoAcceptFriendRequest(self, msg: WxMsg) -> None:
        try:
            xml = ET.fromstring(msg.content)
            v3 = xml.attrib["encryptusername"]
            v4 = xml.attrib["ticket"]
            scene = int(xml.attrib["scene"])
            self.wcf.accept_new_friend(v3, v4, scene)

        except Exception as e:
            self.LOG.error(f"同意好友出错：{e}")

    def sayHiToNewFriend(self, msg: WxMsg) -> None:
        nickName = re.findall(r"你已添加了(.*)，现在可以开始聊天了。", msg.content)
        if nickName:
            # 添加了好友，更新好友列表
            self.allContacts[msg.sender] = nickName[0]
            self.sendTextMsg(f"Hi {nickName[0]}，我自动通过了你的好友请求。", msg.sender)

    def task_send_info(self):
        resp = info.send(self.all_user, self.wxid)
        if resp:
            self.LOG.info("send info success")
        else:
            self.LOG.info("send info failed")

    def task_sync_user(self):
        self.LOG.info("start sync_user")
        self.config.resource["user"] = self.all_user
        self.config.rewrite_reload()
        self.LOG.info("complete sync_user")

    def tasks(self, task_type) -> None:
        receivers = self.config.GROUPS
        if not receivers:
            return
        if task_type == "news":
            resp = News().get_important_news()
        elif task_type == "morning":
            resp = morning_night.zao_an()
        elif task_type == "night":
            resp = morning_night.wan_an()
        else:
            return
        for r in receivers:
            # self.sendTextMsg(news, r, "notify@all")
            self.sendTextMsg(resp, r)




