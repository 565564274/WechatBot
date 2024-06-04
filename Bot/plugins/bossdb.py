```python
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


# 定义一个bossdb类，继承自Base
class BossDB(Base):
    __tablename__ = 'bossdb'

    id = Column(Integer, primary_key=True, autoincrement=True)
    boss_name = Column(String, nullable=False)
    boss_hp = Column(Integer, nullable=False)
    boss_atk = Column(Integer, nullable=False)
    boss_atkper = Column(Integer, nullable=False)
    boss_dod = Column(Integer, nullable=False)
    boss_earntit = Column(String, nullable=False)
    boss_earnexp = Column(Integer, nullable=False)
    boss_earnlevel = Column(Integer, nullable=False)
    boss_earngold = Column(Integer, nullable=False)
    boss_earnling = Column(Integer, nullable=False)
    boss_earncele = Column(Integer, nullable=False)
    boss_earnmagic = Column(Integer, nullable=False)

    @staticmethod
    def get_boss_info(session, id):
        return session.query(BossDB).filter(BossDB.id == id).first()

    @staticmethod
    def update_boss_info(session, boss_name, data):
        boss = session.query(BossDB).filter(BossDB.boss_name == boss_name).first()
        if not boss:
            boss = BossDB(**data)
            session.add(boss)
        else:
            for key, value in data.items():
                setattr(boss, key, value)
        session.commit()

    @staticmethod
    def get_boss_by_name(session, boss_name):
        return session.query(BossDB).filter(BossDB.boss_name == boss_name).first()


# 初始化数据库连接
DATABASE_URL = 'sqlite:///./test.db'  # 你可以更改为你的数据库URL
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)
session = Session()

# 示例用法
# 查询boss信息
boss = BossDB.get_boss_info(session, 1)
print(boss)

# 更新boss信息
data = {
    "boss_name": "Dragon",
    "boss_hp": 1000,
    "boss_atk": 150,
    "boss_atkper": 10,
    "boss_dod": 5,
    "boss_earntit": "Dragon Slayer",
    "boss_earnexp": 500,
    "boss_earnlevel": 5,
    "boss_earngold": 300,
    "boss_earnling": 200,
    "boss_earncele": 100,
    "boss_earnmagic": 50
}
BossDB.update_boss_info(session, "Dragon", data)

# 根据名称查询boss信息
boss = BossDB.get_boss_by_name(session, "Dragon")
print(boss)
```