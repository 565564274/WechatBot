from sqlmodel import create_engine, Session, select
from sqlmodel import asc, desc
from typing import TypeVar, Union, Type

from data.model import *
from utils.root_path import DEFAULT_DATA_PATH
from utils.singleton import singleton


@singleton
class Engine:
    def __init__(self):
        sqlite_file_path = DEFAULT_DATA_PATH / "BotData.db"
        self.engine = create_engine(f"sqlite:///{sqlite_file_path}")
        SQLModel.metadata.create_all(self.engine)

    def insert(self, model_object: SQLModel):
        with Session(self.engine) as session:
            session.add(model_object)
            session.commit()
            session.refresh(model_object)
            session.expunge(model_object)
        return model_object

    def select(self, model_class: Type[SQLModel], **kwargs):
        with Session(self.engine) as session:
            statement = select(model_class)
            for key, value in kwargs.items():
                statement = statement.where(getattr(model_class, key) == value)
            results = session.exec(statement).all()
            return results

    def select_order_by(self, model_class: Type[SQLModel], order_by: Union[str, tuple], limit=False, **kwargs):
        with Session(self.engine) as session:
            statement = select(model_class)
            # 处理 order_by 参数
            if isinstance(order_by, str):
                statement = statement.order_by(getattr(model_class, order_by))
            elif isinstance(order_by, tuple) and len(order_by) == 2:
                field, direction = order_by
                if direction.lower() == "asc":
                    statement = statement.order_by(asc(getattr(model_class, field)))
                elif direction.lower() == "desc":
                    statement = statement.order_by(desc(getattr(model_class, field)))
            if limit:
                statement = statement.limit(limit)
            for key, value in kwargs.items():
                statement = statement.where(getattr(model_class, key) == value)
            results = session.exec(statement).all()
            return results

    def update(self, model_class: Type[SQLModel], model_id: int, **kwargs):
        with Session(self.engine) as session:
            instance = session.get(model_class, model_id)
            if instance:
                for key, value in kwargs.items():
                    setattr(instance, key, value)
                session.commit()
                session.refresh(instance)
                session.expunge(instance)
                return instance
        return False

    def delete(self, model_class: Type[SQLModel], model_id: int):
        with Session(self.engine) as session:
            instance = session.get(model_class, model_id)
            if instance:
                session.delete(instance)
                session.commit()
                return True
        return False























