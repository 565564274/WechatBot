from sqlalchemy import Column, Integer, String, create_engine, literal, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
engine = create_engine('sqlite:///xiuxiandb.db')
Session = sessionmaker(bind=engine)

# 灵力各境界名称
power_name = ['灵力', '仙力', '魔力', '帝源', '混沌之力']

# 境界所需灵力
level_exp = [0, 50, 100, 150, 200, 250, 300, 350, 400, 460, 520, 580, 640, 700, 760, 820, 880, 940,
             1010, 1080, 1150, 1220, 1290, 1360, 1430, 1500, 1570, 1650, 1730, 1810, 1890, 1970, 2050,
             2130, 2210, 2290, 2380, 2470, 2560, 2650, 2740, 2830, 2920, 3010, 3100, 3200, 3300, 3400,
             3500, 3600, 3700, 3800, 3900, 4000, 4100, 4200, 4300, 4400, 4500, 4600, 4700, 4800, 4900,
             5000, 5100, 5200, 5300, 5400, 5500, 5600, 5700, 5800, 6000, 6200, 6400, 6600, 6900, 7200,
             7500, 7800, 8150, 8500, 8850, 9200, 9600, 10000, 10400, 10800, 11200, 11600, 12000, 12400,
             13000, 13800, 14600, 15500, 16500, 17500, 18500, 19500, 20500, 21500, 22500, 23500, 24500,
             25500, 26500, 27500, 28500, 29500, 30500]

# 玩家境界名称
level_name = ['凡人', '炼气第1层', '炼气第2层', '炼气第3层', '炼气第4层', '炼气第5层', '炼气第6层', '炼气第7层',
              '炼气第8层',
              '炼气第9层', '筑基第1层', '筑基第2层', '筑基第3层', '筑基第4层', '筑基第5层', '筑基第6层', '筑基第7层',
              '筑基第8层',
              '筑基第9层', '金丹第1层', '金丹第2层', '金丹第3层', '金丹第4层', '金丹第5层', '金丹第6层', '金丹第7层',
              '金丹第8层',
              '金丹第9层', '元婴第1层', '元婴第2层', '元婴第3层', '元婴第4层', '元婴第5层', '元婴第6层', '元婴第7层',
              '元婴第8层',
              '元婴第9层', '化神第1层', '化神第2层', '化神第3层', '化神第4层', '化神第5层', '化神第6层', '化神第7层',
              '化神第8层',
              '化神第9层', '合体第1层', '合体第2层', '合体第3层', '合体第4层', '合体第5层', '合体第6层', '合体第7层',
              '合体第8层',
              '合体第9层', '大乘第1层', '大乘第2层', '大乘第3层', '大乘第4层', '大乘第5层', '大乘第6层', '大乘第7层',
              '大乘第8层',
              '大乘第9层', '渡劫第1层', '渡劫第2层', '渡劫第3层', '渡劫第4层', '渡劫第5层', '渡劫第6层', '渡劫第7层',
              '渡劫第8层',
              '渡劫第9层', '人仙境初期', '人仙境中期', '人仙境后期', '人仙境圆满', '地仙境初期', '地仙境中期',
              '地仙境后期', '地仙境圆满',
              '天仙境初期', '天仙境中期', '天仙境后期', '天仙境圆满', '金仙境初期', '金仙境中期', '金仙境后期',
              '金仙境圆满', '大罗金仙境初期',
              '大罗金仙境中期', '大罗金仙境后期', '大罗金仙境圆满', '准仙帝境', '准仙帝境圆满', '仙帝境', '仙帝境圆满',
              '天人五衰之仙衰',
              '天人五衰之躯衰', '天人五衰之窍衰', '天人五衰之魂衰', '天人五衰之煞衰', '圣人第1层', '圣人第2层',
              '圣人第3层', '圣人第4层',
              '圣人第5层', '圣人第6层', '圣人第7层', '圣人第8层', '圣人第9层']


class XiuxianDB(Base):
    __tablename__ = 'xiuxiandb'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    group_id = Column(String, nullable=False)
    level = Column(Integer, nullable=False)
    levelname = Column(String, nullable=False)
    experience = Column(Integer, nullable=False)

    @staticmethod
    def level_name(info):
        levelname = ""
        if info.level < 111:
            levelname = level_name[info.level]
        elif 110 < info.level < 10000:
            levelname = f"大帝第{info.level - 110}重天"
        elif info.level >= 10000:
            levelname = "道祖"
        return levelname

    @staticmethod
    def experience_info(info):
        lev = info.level
        exerp = 1000 * (lev - 110) + 30500
        need = 0
        if info.experience < level_exp[lev] and info.level < 111:
            need = level_exp[lev] - info.experience
        elif 110 < info.level and info.experience < exerp:
            need = exerp - info.experience
        else:
            need = 0

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

        return {"need": need, "pwname": pwname}

    @classmethod
    def add_level(cls, value):
        session = Session()
        users = session.query(cls).all()
        for user in users:
            user.level += value
            user.levelname = cls.level_name(user)
            session.add(user)
        session.commit()
        session.close()

    @classmethod
    def add_experience(cls, value):
        session = Session()
        users = session.query(cls).all()
        for user in users:
            user.experience += value
            session.add(user)
        session.commit()
        session.close()

    @classmethod
    def moveback(cls):
        session = Session()
        users = session.query(cls).all()
        for user in users:
            if user.level < 111:
                for i in range(len(level_exp)):
                    if level_exp[i] <= user.experience < level_exp[i + 1]:
                        user.level = i
                        break
                user.levelname = level_name[user.level]
            elif 110 < user.level < 10000:
                user.level = (user.experience - 30500) // 1000 + 110
                user.levelname = cls.level_name(user)
            session.add(user)
        session.commit()
        session.close()


# 创建表
Base.metadata.create_all(engine)
