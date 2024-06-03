from typing import Optional
from sqlmodel import SQLModel, Field


class Chatroom(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    roomid: str = Field(index=True)
    enable: bool = Field(default=True, description="是否开启群功能")
    admin: Optional[str] = Field(default=None, description="群管理wxid")
    ban_keywords: Optional[str] = Field(default=None, description="违禁词")
    status_avoid_revoke: bool = Field(default=True, description="是否开启：防撤回")
    status_ban_keywords: bool = Field(default=True, description="是否开启：违禁词提醒&踢人")
    status_inout_monitor: bool = Field(default=True, description="是否开启：退群监控")


class ChatroomBan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    roomid: str = Field(index=True)
    wxid: str = Field(index=True)
    count: int = Field(default=1, description="违禁词次数")


class MsgHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sender: str
    roomid: str = Field(index=True)
    msg_id: str = Field(index=True)
    ts: str
    type: str
    xml: str
    content: str
    thumb: str
    extra: str
    path: Optional[str]


class GameChengyu(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    roomid: str = Field(index=True)
    wxid: str = Field(index=True)
    score: int = Field(default=1, description="得分")




