from typing import Optional
from sqlmodel import SQLModel, Field


class Chatroom(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    roomid: str = Field(index=True)
    enable: bool = Field(default=False, description="是否响应群消息")
    admin: Optional[str] = Field(default=None, description="群管理")

