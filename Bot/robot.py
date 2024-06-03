import re
import time
import xml.etree.ElementTree as ET
import threading
import copy

from wcferry import Wcf, WxMsg
from queue import Empty
from threading import Thread
from datetime import datetime

from utils.log import logger_manager
from utils.singleton import singleton
from utils.root_path import DEFAULT_TEMP_PATH
from data.bot_data_util import BotData

from Bot.job_mgmt import Job
from Bot.plugins.pokeme import pokeme_reply
from Bot.plugins.qingganyulu import get_yulu
from Bot.plugins.shadiao import shadiao
from Bot.plugins.zhanan_lvcha import zhanan_lvcha
from Bot.plugins.duanzi import duanzi
from Bot.plugins.news import News
from Bot.plugins import lsp
from Bot.plugins import morning_night
from Bot.plugins import chengyu


def new_str(self) -> str:
    s = "=" * 32 * 6 + "\n"
    s += f"{'自己发的:' if self._is_self else ''}"
    s += f"{self.sender}[{self.roomid}]|{self.id}|{datetime.fromtimestamp(self.ts)}|{self.type}|{self.sign}"
    s += f"\n{self.xml.replace(chr(10), '').replace(chr(9), '')}\n"
    s += f"\ncontent: {self.content}" if self.content else ""
    s += f"\nthumb: {self.thumb}" if self.thumb else ""
    s += f"\nextra: {self.extra}" if self.extra else ""
    return s


WxMsg.__str__ = new_str


@singleton
class Robot(Job):

    def __init__(self, config, wcf: Wcf) -> None:
        self.wcf = wcf
        self.bot_data = BotData()
        self.config = config
        self.LOG = logger_manager.logger
        self.wxid = self.wcf.get_self_wxid()
        self.allContacts = self.getAllContacts()
        self.chatroom_member = self.get_all_chatroom_member()
        self.member_monitor()
        self.chatroom_game = {
            "roomid": {"game_name": "", "status": False, "start_time": int(time.time()),
                       "data": {}}
        }

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
            self.check_msg_is_ban_keyword(msg)
            if msg.is_at(self.wxid):
                if self.check_is_admin(msg):
                    # 如果在群里被管理员 @
                    return self.admin(msg)
                else:
                    return self.sendTextMsg("非管理员@我无效", msg.roomid, msg.sender)

            if self.check_is_start_chatroom(msg):
                self.save_msg_to_db(msg)
            else:
                return

            if msg.type == 10000:  # 系统信息
                if "拍了拍我" in msg.content:
                    # 回复拍一拍
                    return self.sendTextMsg(pokeme_reply(), msg.roomid, msg.sender)
                elif "加入了群聊" in msg.content:
                    # 进群提醒
                    return self.when_member_in(msg)
                else:
                    self.LOG.info("msg.type == 10000 的其他消息")
                    return
            elif msg.type == 10002:  # 撤回消息及其它
                return self.when_msg_revoke(msg)
            elif msg.is_text():  # 文本消息
                if self.check_is_in_game(msg):
                    return self.when_game_in_progress(msg)

                if msg.content.startswith("#") or msg.content.startswith("＃"):
                    return self.when_game_start(msg)

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
                pass

    def save_msg_to_db(self, msg: WxMsg):
        def _save(msg: WxMsg):
            # 保存 文字、图片、语音 类型的消息
            if msg.type in [1, 34]:
                self.bot_data.add_msg(msg)
            elif msg.type == 3:
                time.sleep(1)
                path = self.wcf.download_image(msg.id, msg.extra, str(DEFAULT_TEMP_PATH), timeout=10)
                self.bot_data.add_msg(msg, path=path)

        t = threading.Thread(target=_save, args=(msg,))
        t.start()

    def check_is_admin(self, msg: WxMsg) -> bool:
        """
        判断是不是 administrators(创建者) 或者 群管理
        """
        if msg.sender == self.config.ADMIN:
            # administrators(创建者)
            return True
        elif msg.roomid in self.bot_data.chatroom:
            if msg.sender in self.bot_data.chatroom[msg.roomid]["admin"]:
                # 群管理
                return True
        return False

    def check_is_start_chatroom(self, msg: WxMsg) -> bool:
        """
        判断群功能是否开启
        """
        if msg.roomid not in self.bot_data.chatroom:
            # 不在配置的群列表里
            return False
        elif not self.bot_data.chatroom[msg.roomid]["enable"]:
            # 未开启群功能
            return False
        else:
            return True

    def admin(self, msg: WxMsg) -> None:
        """
        处理administrators(创建者)的@消息
        :param msg: 微信消息结构
        """
        q = re.sub(r"@.*?[\u2005|\s]", "", msg.content).replace(" ", "")
        if q == "开启":
            if msg.roomid not in self.bot_data.chatroom:
                self.bot_data.add_chatroom(msg.roomid)
                self.sendTextMsg("群功能已开启，可以开始使用。", msg.roomid, msg.sender)
            elif not self.bot_data.chatroom[msg.roomid]["enable"]:
                self.bot_data.update_chatroom(msg.roomid, enable=True)
                self.sendTextMsg("群功能已开启，可以开始使用。", msg.roomid, msg.sender)
            else:
                self.sendTextMsg("群功能已开启，无需操作。", msg.roomid, msg.sender)
        elif q == "关闭":
            if msg.roomid not in self.bot_data.chatroom:
                self.sendTextMsg("群功能未开启，无需操作。", msg.roomid, msg.sender)
            elif self.bot_data.chatroom[msg.roomid]["enable"]:
                self.bot_data.update_chatroom(msg.roomid, enable=False)
                self.sendTextMsg("群功能已关闭，机器人不再响应。", msg.roomid, msg.sender)
            else:
                self.sendTextMsg("群功能未开启，无需操作。", msg.roomid, msg.sender)
        elif q in ["开启防撤回", "开启违禁词", "开启退群监控"]:
            if q == "开启防撤回":
                if not self.bot_data.chatroom[msg.roomid]["status_avoid_revoke"]:
                    self.bot_data.update_chatroom(msg.roomid, status_avoid_revoke=True)
                    self.sendTextMsg("防撤回已开启", msg.roomid, msg.sender)
                    return
            elif q == "开启违禁词":
                if not self.bot_data.chatroom[msg.roomid]["status_ban_keywords"]:
                    self.bot_data.update_chatroom(msg.roomid, status_ban_keywords=True)
                    self.sendTextMsg("违禁词已开启\nTips:请给机器人设置管理，否则踢人功能将无效", msg.roomid, msg.sender)
                    return
            elif q == "开启退群监控":
                if not self.bot_data.chatroom[msg.roomid]["status_inout_monitor"]:
                    self.bot_data.update_chatroom(msg.roomid, status_inout_monitor=True)
                    self.sendTextMsg("退群监控已开启", msg.roomid, msg.sender)
                    return
            self.sendTextMsg("已开启，无需操作。", msg.roomid, msg.sender)
        elif q in ["关闭防撤回", "关闭违禁词", "关闭退群监控"]:
            if q == "关闭防撤回":
                if self.bot_data.chatroom[msg.roomid]["status_avoid_revoke"]:
                    self.bot_data.update_chatroom(msg.roomid, status_avoid_revoke=False)
                    self.sendTextMsg("防撤回已关闭", msg.roomid, msg.sender)
                    return
            elif q == "关闭违禁词":
                if self.bot_data.chatroom[msg.roomid]["status_ban_keywords"]:
                    self.bot_data.update_chatroom(msg.roomid, status_ban_keywords=False)
                    self.sendTextMsg("违禁词已关闭", msg.roomid, msg.sender)
                    return
            elif q == "关闭退群监控":
                if self.bot_data.chatroom[msg.roomid]["status_inout_monitor"]:
                    self.bot_data.update_chatroom(msg.roomid, status_inout_monitor=False)
                    self.sendTextMsg("退群监控已关闭", msg.roomid, msg.sender)
                    return
            self.sendTextMsg("已关闭，无需操作。", msg.roomid, msg.sender)
        elif q == "状态":
            if msg.roomid not in self.bot_data.chatroom:
                return self.sendTextMsg("群功能未曾开启，无法查看状态", msg.roomid, msg.sender)
            self.reply_chatroom_func_status(msg)
        elif q.startswith("添加违禁词") or q.startswith("删除违禁词"):
            if not q[5:]:
                return self.sendTextMsg("请输入：\n添加违禁词 XXX\n或者\n删除违禁词 XXX", msg.roomid, msg.sender)
            else:
                if q.startswith("添加违禁词"):
                    new = copy.deepcopy(self.bot_data.chatroom[msg.roomid]["ban_keywords"])
                    new.append(q[5:])
                    self.bot_data.update_chatroom(msg.roomid, ban_keywords="|".join(new))
                    return self.sendTextMsg(f"已添加违禁词【{q[5:]}】", msg.roomid, msg.sender)
                elif q.startswith("删除违禁词"):
                    if q[5:] not in self.bot_data.chatroom[msg.roomid]["ban_keywords"]:
                        return self.sendTextMsg(f"违禁词{q[5:]}不存在", msg.roomid, msg.sender)
                    else:
                        new = copy.deepcopy(self.bot_data.chatroom[msg.roomid]["ban_keywords"])
                        new.remove(q[5:])
                        self.bot_data.update_chatroom(msg.roomid, ban_keywords="|".join(new))
                        return self.sendTextMsg(f"已删除违禁词【{q[5:]}】", msg.roomid, msg.sender)
        else:
            self.sendTextMsg("未识别指令", msg.roomid, msg.sender)

    def when_member_in(self, msg: WxMsg) -> None:
        try:
            inviter = msg.content.split("邀请")[0].replace("\"", "")
            member = msg.content.split("邀请")[-1].replace("加入了群聊", "").replace("\"", "")
        except Exception as e:
            self.LOG.error(str(e))
            return
        self.wcf.send_rich_text(
            name="",
            account="",
            title="🎉🎉欢迎进群🎉🎉",
            digest=f"邀请人👉{inviter}\n新朋友👉{member}",
            url="https://ez4leon.top/",
            thumburl="",
            receiver=msg.roomid
        )

    def get_all_chatroom_member(self) -> dict:
        roomid_list = [roomid for roomid in self.bot_data.chatroom.keys() if self.bot_data.chatroom[roomid]["enable"]]
        chatroom_member = {}
        for roomid in roomid_list:
            chatroom_member[roomid] = self.wcf.get_chatroom_members(roomid)
        return chatroom_member

    def member_monitor(self) -> None:
        def _monitor():
            first = True
            while True:
                if first:
                    time.sleep(10)
                    self.chatroom_member = self.get_all_chatroom_member()
                    first = False
                    continue
                now = self.get_all_chatroom_member()
                for roomid in self.chatroom_member.keys():
                    if not self.bot_data.chatroom[roomid]["status_inout_monitor"]:
                        # 未开启退群监控
                        continue
                    if roomid not in now:
                        # 最新的chatroom_member无对应roomid，因为群功能才开启
                        continue
                    else:
                        for wxid in self.chatroom_member[roomid].keys():
                            if wxid not in now[roomid].keys():
                                self.when_member_out(roomid, self.chatroom_member[roomid][wxid])
                # 更新chatroom_member
                self.chatroom_member = now
                time.sleep(5)

        t = threading.Thread(target=_monitor, args=())
        t.start()

    def when_member_out(self, roomid: str, name: str) -> None:
        self.sendTextMsg(f"【{name}】退出了群聊，江湖再见！", roomid)

    def when_msg_revoke(self, msg: WxMsg) -> None:
        def _find_msg(msg: WxMsg, msg_id: str):
            find_msg = None
            for i in range(5):
                find_msg = self.bot_data.get_msg(msg.roomid, msg_id)
                if not find_msg:
                    if i == 4:
                        return
                    time.sleep(1)
                    continue
                else:
                    break
            self.sendTextMsg("啧...让我看看你撤回了什么", msg.roomid)
            name = self.wcf.get_alias_in_chatroom(msg.sender, msg.roomid)
            time.sleep(0.5)
            if find_msg.type == "1":
                # 文本
                return self.sendTextMsg(f"【{name}】撤回了文本消息👇\n{find_msg.content}", msg.roomid)
            elif find_msg.type == "3":
                # 图片
                if find_msg.path:
                    self.sendTextMsg(f"【{name}】撤回了图片消息👇", msg.roomid)
                    self.sendImageMsg(find_msg.path, msg.roomid)
                else:
                    self.sendTextMsg(f"【{name}】撤回的图片消息没找到[苦涩]", msg.roomid)
                return
            elif find_msg.type == "34":
                # 语音
                audio_path = self.wcf.get_audio_msg(int(msg_id), str(DEFAULT_TEMP_PATH), timeout=30)
                if not audio_path:
                    return
                else:
                    self.sendTextMsg(f"【{name}】撤回了语音消息👇", msg.roomid)
                    self.sendFileMsg(audio_path, msg.roomid)
                    return
            else:
                # todo: 可以适配视频消息
                return

        if not self.bot_data.chatroom[msg.roomid]["status_avoid_revoke"]:
            # 未开启防撤回
            return
        try:
            xml = ET.fromstring(msg.content)
            if xml.tag == "sysmsg" and xml.attrib["type"] == "revokemsg":
                msg_id = xml.find('.//newmsgid').text
                t = threading.Thread(target=_find_msg, args=(msg, msg_id))
                t.start()
            else:
                self.LOG.info("msg.type == 10002 的其他消息")
        except Exception as e:
            self.LOG.error(f"when_msg_revoke出错：{e}")

    def check_msg_is_ban_keyword(self, msg: WxMsg) -> None:
        def _check(msg: WxMsg):
            if msg.type != 1:
                return
            ban_keywords_list = self.bot_data.chatroom[msg.roomid]["ban_keywords"]
            for ban_keywords in ban_keywords_list:
                if ban_keywords in msg.content:
                    ban = self.bot_data.get_ban(msg.roomid, msg.sender)
                    if not ban:
                        self.bot_data.add_ban(msg.roomid, msg.sender)
                        count = 1
                    else:
                        count = ban.count + 1
                    if count < 3:
                        self.bot_data.update_ban(msg.roomid, msg.sender, count=count)
                        self.sendTextMsg(f"🈲🈲🈲\n抱歉，你发表了不当言论，已累计{count}次，请谨言慎行，累计3次将踢出群聊。", msg.roomid, msg.sender)
                    else:
                        self.bot_data.update_ban(msg.roomid, msg.sender, count=0)
                        self.sendTextMsg(f"🈲🈲🈲\n抱歉，你发表了不当言论，已累计{count}次，现将你移出群聊。\n[再见][再见][再见]️", msg.roomid, msg.sender)
                        self.wcf.del_chatroom_members(msg.roomid, msg.sender)

        if msg.roomid not in self.bot_data.chatroom:
            # 未开启群功能
            return
        elif not self.bot_data.chatroom[msg.roomid]["status_ban_keywords"]:
            # 未开启违禁词
            return
        elif self.check_is_admin(msg):
            # 管理员无视
            return
        t = threading.Thread(target=_check, args=(msg,))
        t.start()

    def reply_chatroom_func_status(self, msg: WxMsg) -> None:
        status = [
            self.bot_data.chatroom[msg.roomid]["enable"],
            self.bot_data.chatroom[msg.roomid]["status_avoid_revoke"],
            self.bot_data.chatroom[msg.roomid]["status_ban_keywords"],
            self.bot_data.chatroom[msg.roomid]["status_inout_monitor"],
        ]
        content = (
            f'[{"✔️" if status[0] else "✖️"}] 群功能\n'
            f'[{"✔️" if status[1] else "✖️"}] 防撤回\n'
            f'[{"✔️" if status[2] else "✖️"}] 违禁词\n'
            f'[{"✔️" if status[3] else "✖️"}] 退群监控'
        )
        self.sendTextMsg(content, msg.roomid)


    def check_is_in_game(self, msg: WxMsg) -> bool:
        """
        判断群是否处于游戏中
        """
        if msg.roomid not in self.chatroom_game:
            # 不在配置的群列表里
            self.chatroom_game[msg.roomid] = {"game_name": "", "status": False}
            return False
        elif not self.chatroom_game[msg.roomid]["status"]:
            # 未开启群功能
            return False
        else:
            return True

    def when_game_start(self, msg: WxMsg) -> None:
        def _count_down(msg: WxMsg):
            if self.chatroom_game[msg.roomid]["game_name"] == "chengyu":
                while True:
                    if not self.chatroom_game[msg.roomid]["status"]:
                        return
                    if (int(time.time()) - self.chatroom_game[msg.roomid]["start_time"]) >= 60:
                        answer = self.chatroom_game[msg.roomid]["data"]["answer"]
                        self.sendTextMsg(f"60s内无正确答案，自动结束！\n正确答案：{answer}", msg.roomid)
                        self.chatroom_game[msg.roomid] = {"game_name": "", "status": False}
                        return
                    else:
                        time.sleep(1)
                        continue
            return

        if msg.content[1:] == "看图猜成语":
            status, data = chengyu.chengyu()
            if status:
                self.sendTextMsg("【看图猜成语】已开始，请直接输入成语作答，60s后自动结束！", msg.roomid)
                self.chatroom_game[msg.roomid] = {"game_name": "chengyu", "status": True, "start_time": int(time.time()),
                                                  "data": {"answer": data["answer"]}}
                self.sendImageMsg(data["pic"], msg.roomid)
                t = threading.Thread(target=_count_down, args=(msg,))
                t.start()
            else:
                return self.sendTextMsg(data, msg.roomid)

    def when_game_in_progress(self, msg: WxMsg) -> None:
        if msg.content == "结束游戏":
            self.chatroom_game[msg.roomid] = {"game_name": "", "status": False}
            self.sendTextMsg("游戏已结束", msg.roomid)
        if self.chatroom_game[msg.roomid]["game_name"] == "chengyu":
            if msg.content == self.chatroom_game[msg.roomid]["data"]["answer"]:
                self.chatroom_game[msg.roomid] = {"game_name": "", "status": False}
                status, data = chengyu.chengyu_answer(msg.content)
                name = self.wcf.get_alias_in_chatroom(msg.sender, msg.roomid)
                resp = f"🎉🎉恭喜【{name}】答对！🎉🎉"
                if status:
                    explain = (f'\n'
                               f'【答案】{data["cycx"].split("-")[0]}\n'
                               f'【拼音】{data["cycx"].split("-")[1]}\n'
                               f'【解释】{data["cyjs"]}\n'
                               f'【出处】{data["cycc"]}\n'
                               f'【造句】{data["cyzj"]}\n')
                else:
                    explain = ""
                self.sendTextMsg(resp + explain, msg.roomid)
                game_data = self.bot_data.get_game_chengyu(roomid=msg.roomid, wxid=msg.sender)
                if not game_data:
                    self.bot_data.add_game_chengyu(msg.roomid, msg.sender)
                else:
                    self.bot_data.update_game_chengyu(msg.roomid, msg.sender, score=game_data.score + 1)
                all_game_data = self.bot_data.get_game_chengyu(all_data=True, roomid=msg.roomid)
                resp = "[排名][得分][昵称]"
                for i in range(len(all_game_data)):
                    name = self.wcf.get_alias_in_chatroom(all_game_data[i].wxid, all_game_data[i].roomid)
                    resp += f"\n{i}.💯[{all_game_data[i].score}]👉{name}"
                self.sendTextMsg(resp, msg.roomid)
                return
            else:
                return
        return






    ################################################################
    ################################################################

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
        receivers = self.bot_data.chatroom.keys()
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
            # todo: 待开发开关及自定义事件
            pass
            self.sendTextMsg(resp, r)




