import os
import time

from datetime import datetime, timedelta
from random import randint

from wcferry import WxMsg
from data.bot_data_util import BotData



levelname = ['凡人', '练气期', '筑基期', '金丹期', '元婴期', '化神期', '合体期', '大乘期', '渡劫期', '人仙境', '地仙境',
             '天仙境', '金仙境', '大罗金仙境', '准仙帝', '仙帝', '天人五衰境', '圣人', '大帝', '神境【预告】/ 魔境【预告】',
             '神魔合一境【预告】', '道祖']
level_exp = [
    0, 50, 100, 150, 200, 250, 300, 350, 400,  # /* 炼气 */
    460, 520, 580, 640, 700, 760, 820, 880, 940,  # /* 筑基 */
    1010, 1080, 1150, 1220, 1290, 1360, 1430, 1500, 1570,  # /* 金丹 */
    1650, 1730, 1810, 1890, 1970, 2050, 2130, 2210, 2290,  # /* 元婴 */
    2380, 2470, 2560, 2650, 2740, 2830, 2920, 3010, 3100,  # /* 化神 */
    3200, 3300, 3400, 3500, 3600, 3700, 3800, 3900, 4000,  # /* 合体 */
    4100, 4200, 4300, 4400, 4500, 4600, 4700, 4800, 4900,  # /* 大乘 */
    5000, 5100, 5200, 5300, 5400, 5500, 5600, 5700, 5800,  # /* 渡劫 */
    6000, 6200, 6400, 6600,  # /* 人仙 */
    6900, 7200, 7500, 7800,  # /* 地仙 */
    8150, 8500, 8850, 9200,  # /* 天仙 */
    9600, 10000, 10400, 10800,  # /* 金仙 */
    11200, 11600, 12000, 12400,  # /* 大罗金仙 */
    13000, 13800,  # /* 准仙帝 */
    14600, 15500,  # /* 仙帝 */
    16500, 17500, 18500, 19500, 20500,  # /* 天人五衰 */
    21500, 22500, 23500, 24500, 25500, 26500, 27500, 28500, 29500, 30500  # /* 圣人 */
]
master_cd= False #主人是否需要cd
cdtime_xiuxian= 2 * 60#修炼的冷却时间,单位分钟
cdtime_break= 0.5 * 60#突破的冷却时间,单位分钟
# cdtime_down= 6 #闭关冷却,单位小时
# down_up= 800 #闭关保底提升值
# down_ave= 1000 #闭关提升波动幅度
pill_up= 25 #丹药提升灵力值
pill_down= 7 #丹药降低灵力值
pill_per= 40 #丹药成功概率
xiuxian_up= 5 #修仙提升保底
xiuxian_ave= 10 #修仙提升波动幅度
group_limit= 30 #群排行人数限制
all_limit= 100 #全服排行人数限制


power_name = ['灵力', '仙力', '魔力', '帝源', '混沌之力']



class Xiuxian:
    def __init__(self):
        self.name = '轻量修炼'
        self.dsc = '轻量修仙'
        self.event = 'message'
        self.priority = -999
        self.rule = [
            {'reg': '^#?(我的境界|查看境界)$', 'fnc': self.view},
            {'reg': '^#?(修炼|修仙|服用丹药)$', 'fnc': self.xiuxian},
            {'reg': '^#?突破$', 'fnc': self.break_through},
            {'reg': '^#?(修仙|修炼)?境界列表$', 'fnc': self.list_levels},
            {'reg': '^#?排行榜$', 'fnc': self.rankings},
            {'reg': '^#?我要境界(.*)$', 'fnc': self.giveme_level},
            {'reg': '^#?我要灵力(.*)$', 'fnc': self.giveme_exp},
            {'reg': '^#?(修仙者|修炼者|用户)(人数|数量)$', 'fnc': self.numxiuxian},
            {'reg': '^#?我的id$', 'fnc': self.myid},
            {'reg': '#?全服(排行榜|排名)$', 'fnc': self.allrank},
            {'reg': '#?全服加灵力(.*)', 'fnc': self.giveall_exp},
            {'reg': '#?全服加境界(.*)', 'fnc': self.giveall_level},
            {'reg': '#?开始压缩(.*)', 'fnc': self.moveback}
        ]
        self.bot_data = BotData()

    def getUserInfo(self, msg: WxMsg):
        user_data = self.bot_data.get_game_xiuxian(roomid=msg.roomid, wxid=msg.sender)
        if not user_data:
            self.bot_data.add_game_xiuxian(roomid=msg.roomid, wxid=msg.sender)
        user_data = self.bot_data.get_game_xiuxian(roomid=msg.roomid, wxid=msg.sender)
        return user_data

    def updateUserInfo(self, msg: WxMsg, **kwargs):
        return self.bot_data.update_game_xiuxian(roomid=msg.roomid, wxid=msg.sender, **kwargs)

    def view(self, msg: WxMsg):
        user_data = self.getUserInfo(msg)
        need, pwname = self.experience_need(user_data)
        return (
            f'>境界:{user_data.levelname},\n'
            f'>{pwname}:{user_data.experience},\n'
            f'>您还需要:{need}点{pwname}突破下一境界')

    def xiuxian(self, msg: WxMsg):
        user_data = self.getUserInfo(msg)
        now = int(time.time())
        last_xiuxian = user_data.last_xiuxian
        if last_xiuxian:
            if (now - last_xiuxian) < cdtime_xiuxian:
                return f'您还在闭关中,还有{now - last_xiuxian:.1f}秒cd'

        exp = xiuxian_up + randint(0, xiuxian_ave)
        user_data = self.updateUserInfo(msg,
                                        experience=user_data.experience + exp,
                                        last_xiuxian=now,
                                        )
        need, pwname = self.experience_need(user_data)

        return (f'恭喜你获得了{exp}点${pwname}\n'
         f'>境界:{user_data.levelname}\n'
         f'>{pwname}:{user_data.experience}\n'
         f'>您还需要:{need}点{pwname}突破下一境界')

        msg = [segment.at(e.user_id),
               f'\n\n#id:{user_data["id"]},\n>境界:{user_data["levelname"]},\n>{pwname}:{user_data["experience"]},\n>您还需要:{need}点{pwname}突破下一境界']
        if len(user_id) > 30:
            msg.append(isqbot.btn)
        return e.reply(msg)

    @staticmethod
    def experience_need(info):
        # 突破下一个境界所需灵力
        lev = info.level
        exerp = 1000 * (lev - 110) + 30500
        need = 0
        if info.experience < level_exp[lev] and info.level < 111:
            need = level_exp[lev] - info.experience
        elif 110 < info.level and info.experience < exerp:
            need = exerp - info.experience
        else:
            need = 0

        # 灵力名称
        pwname = 0
        if info.level < 73:
            pwname = power_name[0]
        elif 72 < info.level < 111:
            pwname = power_name[1]
        elif info.experience < 0:
            pwname = power_name[2]
        elif 110 < info.level < 10000:
            pwname = power_name[3]
        elif info.level >= 10000:
            pwname = power_name[4]

        return need, pwname






    def moveback(self, msg: WxMsg):
        if not e.isMaster:
            return False
        self.bot_data.moveback()
        e.reply('压缩完成')

    def clear(self, msg: WxMsg):
        dirpath = os.path.join(os.getcwd(), 'data/wind-db/xiuxiandata.db')
        if os.path.exists(dirpath):
            for file in os.listdir(dirpath):
                filepath = os.path.join(dirpath, file)
                if os.path.isfile(filepath):
                    os.unlink(filepath)
                elif os.path.isdir(filepath):
                    # Recursively delete directory (function not defined in original code)
                    pass
            os.rmdir(dirpath)
        e.reply('清除成功！！')

    def myid(self, msg: WxMsg):
        user_id = str(e.user_id)
        if len(user_id) > 30:
            btn = isqbot.btn
        group_id = str(e.group_id)
        user_data = self.bot_data.getUserInfo(user_id)
        if user_data is None:
            return e.reply('\n\n#请先使用【修仙】自动分配id')
        if group_id not in user_data['group_id']:
            user_data['group_id'] += ',' + group_id
        if len(user_id) > 30:
            return e.reply([segment.at(e.user_id), f'\n\n#你的id是:{user_data["id"]}', btn])
        return e.reply([segment.at(e.user_id), f'\n\n#你的id是:{user_data["id"]}'])

    def numxiuxian(self, msg: WxMsg):
        e.reply(str(self.bot_data.getMaxId()))

    def giveme_level(self, msg: WxMsg):
        user_id = str(e.user_id)
        if len(user_id) > 30:
            btn = isqbot.btn
        if not e.isMaster:
            if len(user_id) > 30:
                return e.reply(['哈哈，你也想要我的境界吗，咦，不给你，哈哈哈哈,🤣👉🏻🤡', btn])
            return e.reply('哈哈，你也想要我的境界吗，咦，不给你，哈哈哈哈,🤣👉🏻🤡')
        numreg = re.compile(r'[1-9][0-9]{0,12}')
        numret = int(numreg.search(e.msg).group())
        group_id = str(e.group_id)
        user_data = self.bot_data.getUserInfo(user_id)
        if user_data is None:
            user_data = {
                "experience": 0,
                "level": 0,
                "levelname": '凡人',
                "group_id": group_id
            }
            self.bot_data.updateUserInfo(user_id, user_data)
            user_data = self.bot_data.getUserInfo(user_id)

        if group_id not in user_data['group_id']:
            user_data['group_id'] += ',' + group_id

        user_data['level'] += numret
        user_data['levelname'] = self.bot_data.levelName(user_data)
        user_data.save()
        e.reply([segment.at(e.user_id), f'恭喜您，获得了境界{numret}层'])

        need, pwname = self.bot_data.experience(user_data)
        msg = [segment.at(e.user_id),
               f'\n\n#id:{user_data["id"]},\n>境界:{user_data["levelname"]},\n>{pwname}:{user_data["experience"]},\n>您还需要:{need}点{pwname}突破下一境界']
        if len(user_id) > 30:
            msg.append(btn)
        return e.reply(msg)

    def giveme_exp(self, msg: WxMsg):
        user_id = str(e.user_id)
        if len(user_id) > 30:
            btn = isqbot.btn
        if not e.isMaster:
            if len(user_id) > 30:
                return e.reply(['哈哈，你也想要我的灵力吗，咦，不给你，哈哈哈哈,🤣👉🏻🤡', btn])
            return e.reply('哈哈，你也想要我的灵力吗，咦，不给你，哈哈哈哈,🤣👉🏻🤡')
        numreg = re.compile(r'[1-9][0-9]{0,12}')
        numret = int(numreg.search(e.msg).group())
        group_id = str(e.group_id)
        user_data = self.bot_data.getUserInfo(user_id)
        if user_data is None:
            user_data = {
                "experience": 0,
                "level": 0,
                "levelname": '凡人',
                "group_id": group_id
            }
            self.bot_data.updateUserInfo(user_id, user_data)
            user_data = self.bot_data.getUserInfo(user_id)

        if group_id not in user_data['group_id']:
            user_data['group_id'] += ',' + group_id

        user_data['experience'] += numret
        user_data.save()
        e.reply([segment.at(e.user_id), f'恭喜您，获得了灵力{numret}点'])

        need, pwname = self.bot_data.experience(user_data)
        msg = [segment.at(e.user_id),
               f'\n\n#id:{user_data["id"]},\n>境界:{user_data["levelname"]},\n>{pwname}:{user_data["experience"]},\n>您还需要:{need}点{pwname}突破下一境界']
        if len(user_id) > 30:
            msg.append(btn)
        return e.reply(msg)


    def list_levels(self, msg: WxMsg):
        e.reply('\n'.join([f'{i + 1}:{v}' for i, v in enumerate(levelname)]))

    def allrank(self, msg: WxMsg):
        res = self.bot_data.getAllRank()
        if not res:
            return e.reply('无人修仙')
        msgs = []
        for i, v in enumerate(res):
            msgs.append(f'{i + 1}:{v["name"]}({v["levelname"]})')
        e.reply('\n'.join(msgs))

    def rankings(self, msg: WxMsg):
        res = self.bot_data.getRank()
        if not res:
            return e.reply('无人修仙')
        msgs = []
        for i, v in enumerate(res):
            msgs.append(f'{i + 1}:{v["name"]}({v["levelname"]})')
        e.reply('\n'.join(msgs))

    def giveall_exp(self, msg: WxMsg):
        if not e.isMaster:
            return False
        numreg = re.compile(r'[1-9][0-9]{0,12}')
        numret = int(numreg.search(e.msg).group())
        self.bot_data.giveAllExp(numret)
        e.reply('全服加灵力完成')

    def giveall_level(self, msg: WxMsg):
        if not e.isMaster:
            return False
        numreg = re.compile(r'[1-9][0-9]{0,12}')
        numret = int(numreg.search(e.msg).group())
        self.bot_data.giveAllLevel(numret)
        e.reply('全服加境界完成')



    def break_through(self, msg: WxMsg):
        user_id = str(e.user_id)
        group_id = str(e.group_id)
        user_data = self.bot_data.getUserInfo(user_id)
        if user_data is None:
            user_data = {
                "experience": 0,
                "level": 0,
                "levelname": '凡人',
                "group_id": group_id
            }
            self.bot_data.updateUserInfo(user_id, user_data)
            user_data = self.bot_data.getUserInfo(user_id)

        if group_id not in user_data['group_id']:
            user_data['group_id'] += ',' + group_id
            user_data.save()
            user_data = self.bot_data.getUserInfo(user_id)

        delta = timedelta(seconds=cdtime_break)
        now = datetime.now()
        last_break = user_data.get('last_break', now - delta)
        if (now - last_break).total_seconds() < cdtime_break:
            return e.reply(f'请等待冷却时间，{cdtime_break // 60}分钟后再来')

        need, pwname = self.bot_data.experience(user_data)
        if user_data['experience'] < need:
            return e.reply(f'您的灵力不足，无法突破')

        success_chance = xiuxian_ave / 100
        if randint(1, 100) <= success_chance:
            user_data['level'] += 1
            user_data['levelname'] = self.bot_data.levelName(user_data)
            user_data['experience'] = 0
            user_data['last_break'] = now
            user_data.save()
            e.reply([segment.at(e.user_id), f'恭喜您成功突破到{user_data["levelname"]}'])
        else:
            user_data['last_break'] = now
            user_data.save()
            e.reply([segment.at(e.user_id), '突破失败，请稍后再试'])
