# -*- encoding:utf-8 -*-
import threading
import signal

from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from wcferry import Wcf

from utils import config
from utils.log import logger_manager
from fast_api.statics.static_api import static_app
from Bot.robot import Robot


logger = logger_manager.logger
wcf = Wcf(debug=True)


def handler(sig, frame):
    wcf.cleanup()
    logger.info("signal shutdown done")
    exit(0)


signal.signal(signal.SIGINT, handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    robot = Robot(config, wcf)
    robot.LOG.info(f"WeChatRobot成功启动···")

    # 机器人启动发送测试消息
    robot.sendTextMsg("机器人启动成功！", "filehelper")

    # 接收消息
    robot.enableReceivingMsg()  # 加队列

    robot.onEveryTime("08:00", robot.task_send_info)
    robot.onEveryTime("20:00", robot.task_send_info)
    robot.onEveryMinutes(30, robot.task_sync_user)

    # 让机器人一直跑
    schedule_thread = threading.Thread(target=robot.keepRunningAndBlockProcess)
    schedule_thread.daemon = True
    schedule_thread.start()
    logger.info("startup done")
    yield
    robot.task_sync_user()
    wcf.cleanup()
    logger.info("shutdown done")


app = FastAPI(docs_url=None, redoc_url=None, lifespan=lifespan)
static_dir = Path(__file__).parents[0] / "statics"
app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.include_router(static_app.router, prefix="", tags=[])


@app.get("/get_msg_types")
async def get_msg_types():
    types = wcf.get_msg_types()
    return types


@app.get("/get_contacts")
async def get_contacts():
    contacts = wcf.get_contacts()
    return contacts


@app.get("/get_user_info")
async def get_user_info():
    user_info = wcf.get_user_info()
    return user_info


@app.get("/get_friends")
async def get_friends():
    friends = wcf.get_friends()
    return friends


@app.get("/get_info_by_wxid")
async def get_info_by_wxid(wxid: str):
    info = wcf.get_info_by_wxid(wxid)
    return info


@app.get("/get_chatroom_members")
async def get_chatroom_members(roomid: str):
    members = wcf.get_chatroom_members(roomid)
    return members


@app.get("/get_alias_in_chatroom")
async def get_alias_in_chatroom(wxid: str, roomid: str):
    alias = wcf.get_alias_in_chatroom(wxid, roomid)
    return alias


@app.post("/send_text")
async def send_text(msg: str, receiver: str, aters: Optional[str] = ""):
    status = wcf.send_text(msg, receiver, aters)
    return status


@app.post("/send_image")
async def send_image(path: str, receiver: str):
    status = wcf.send_image(path, receiver)
    return status


@app.post("/send_file")
async def send_file(path: str, receiver: str):
    status = wcf.send_file(path, receiver)
    return status


@app.post("/send_xml")
async def send_xml(receiver: str, xml: str, type: int, path: str = None):
    status = wcf.send_xml(receiver, xml, type, path)
    return status


@app.post("/send_emotion")
async def send_emotion(path: str, receiver: str):
    status = wcf.send_emotion(path, receiver)
    return status


@app.post("/send_rich_text")
async def send_rich_text(name: str, account: str, title: str, digest: str, url: str, thumburl: str, receiver: str):
    status = wcf.send_rich_text(name, account, title, digest, url, thumburl, receiver)
    return status


@app.post("/send_pat_msg")
async def send_pat_msg(roomid: str, wxid: str):
    status = wcf.send_pat_msg(roomid, wxid)
    return status


@app.post("/forward_msg")
async def forward_msg(id: int, receiver: str):
    status = wcf.forward_msg(id, receiver)
    return status


@app.post("/receive_transfer")
async def receive_transfer(wxid: str, transferid: str, transactionid: str):
    status = wcf.receive_transfer(wxid, transferid, transactionid)
    return status


@app.post("/revoke_msg")
async def revoke_msg(id: int):
    status = wcf.revoke_msg(id)
    return status


@app.post("/add_chatroom_members")
async def add_chatroom_members(roomid: str, wxids: str):
    status = wcf.add_chatroom_members(roomid, wxids)
    return status


@app.post("/del_chatroom_members")
async def del_chatroom_members(roomid: str, wxids: str):
    status = wcf.del_chatroom_members(roomid, wxids)
    return status


@app.post("/invite_chatroom_members")
async def invite_chatroom_members(roomid: str, wxids: str):
    status = wcf.invite_chatroom_members(roomid, wxids)
    return status


