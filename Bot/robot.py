import re
import time
import xml.etree.ElementTree as ET

from wcferry import Wcf, WxMsg
from queue import Empty
from threading import Thread
from datetime import datetime

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


def new_str(self) -> str:
    s = "=" * 32 * 6 + "\n"
    s += f"{'自己发的:' if self._is_self else ''}"
    s += f"{self.sender}[{self.roomid}]|{self.id}|{datetime.fromtimestamp(self.ts)}|{self.type}|{self.sign}"
    s += f"\n{self.xml.replace(chr(10), '').replace(chr(9), '')}\n"
    s += f"\ncontent: {self.content}" if self.thumb else ""
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
            # 如果在群里被administrators(创建者) @
            if msg.is_at(self.wxid) and msg.sender == self.config.ADMIN:
                return self.admin(msg)
            if msg.roomid not in self.config.GROUPS:  # 不在配置的响应的群列表里，忽略
                return
            # 如果在群里被非administrators(创建者) @
            if msg.is_at(self.wxid):  # 被@
                # self.toAt(msg)
                self.sendTextMsg("非创建者@我无效", msg.roomid, msg.sender)

            else:  # 其他消息
                if msg.type == 10000:  # 系统信息
                    if "拍了拍我" in msg.content:
                        # 1.回复拍一拍
                        return self.sendTextMsg(pokeme_reply(), msg.roomid, msg.sender)
                    else:
                        self.LOG.info("msg.type == 10000 的其他消息")
                        return
                elif msg.is_text():  # 文本消息
                    if msg.content in ["舔狗日记", "毒鸡汤", "社会语录"]:
                        # 2.情感语录
                        return self.sendTextMsg(get_yulu(msg.content), msg.roomid, msg.sender)
                    elif msg.content in ["疯狂星期四", "彩虹屁", "朋友圈", "朋友圈文案"]:
                        # 3.傻屌语录
                        return self.sendTextMsg(shadiao(msg.content), msg.roomid, msg.sender)
                    elif msg.content in ["渣男", "绿茶"]:
                        # 4.渣男&绿茶语录
                        return self.sendTextMsg(zhanan_lvcha(msg.content), msg.roomid, msg.sender)
                    elif msg.content in ["段子"]:
                        # 5.段子
                        return self.sendTextMsg(duanzi(), msg.roomid, msg.sender)
                    elif msg.content in lsp.mark:
                        status, resp, msg_type = lsp.lsp(msg.content)
                        if status:
                            if msg_type == "image":
                                return self.sendImageMsg(resp, msg.roomid)
                            else:
                                return self.sendFileMsg(resp, msg.roomid)
                        else:
                            return self.sendTextMsg(resp, msg.roomid)


                else:
                    return
                self.toChengyu(msg)

            return  # 处理完群聊信息，后面就不需要处理了

        # 非群聊信息，按消息类型进行处理
        if msg.type == 37:  # 好友请求
            self.autoAcceptFriendRequest(msg)

        elif msg.type == 10000:  # 系统信息
            self.sayHiToNewFriend(msg)

        elif msg.type == 0x01:  # 文本消息
            # 让配置加载更灵活，自己可以更新配置。也可以利用定时任务更新。
            if msg.from_self():
                if msg.content == "^更新$":
                    self.config.reload()
                    self.LOG.info("已更新")
            else:
                self.toChitchat(msg)  # 闲聊

    def admin(self, msg: WxMsg) -> None:
        """
        处理administrators(创建者)的@消息
        :param msg: 微信消息结构
        :return: 处理状态，`True` 成功，`False` 失败
        """
        q = re.sub(r"@.*?[\u2005|\s]", "", msg.content).replace(" ", "")
        if q == "新增群聊":
            if msg.roomid not in self.config.GROUPS:
                self.config.resource["groups"]["enable"].append(msg.roomid)
                self.config.rewrite_reload()
                self.sendTextMsg("群聊已添加，可以开始使用。", msg.roomid, msg.sender)
            else:
                self.sendTextMsg("群聊已存在，无需操作。", msg.roomid, msg.sender)
        elif q == "删除群聊":
            if msg.roomid in self.config.GROUPS:
                self.config.resource["groups"]["enable"].remove(msg.roomid)
                self.config.rewrite_reload()
                self.sendTextMsg("群聊已删除，机器人不再响应。", msg.roomid, msg.sender)
            else:
                self.sendTextMsg("群聊未添加，无需操作。", msg.roomid, msg.sender)
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

    def sendFileMsg(self, file_path: str, receiver: str) -> None:
        """ 发送消息
        :param file_path:
        :param receiver: 接收人wxid或者群id
        """
        self.LOG.info(f"To {receiver}: {file_path}")
        status = self.wcf.send_file(file_path, receiver)
        if status != 0:
            self.sendTextMsg("发送文件失败", receiver)

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




