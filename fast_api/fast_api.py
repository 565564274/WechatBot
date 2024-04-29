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

    # 每天 7 点发送天气预报
    # robot.onEveryTime("07:00", weather_report, robot=robot)

    # 每天 7:30 发送新闻
    robot.onEveryTime("07:30", robot.newsReport)

    # 每天 16:30 提醒发日报周报月报
    # robot.onEveryTime("16:30", ReportReminder.remind, robot=robot)

    # 让机器人一直跑
    schedule_thread = threading.Thread(target=robot.keepRunningAndBlockProcess)
    schedule_thread.daemon = True
    schedule_thread.start()
    logger.info("startup done")
    yield
    wcf.cleanup()
    logger.info("shutdown done")


app = FastAPI(docs_url=None, redoc_url=None, lifespan=lifespan)
static_dir = Path(__file__).parents[0] / "statics"
app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.include_router(static_app.router, prefix="", tags=[])


@app.get("/get_friends")
async def get_friends():
    friends = wcf.get_friends()
    return friends


@app.get("/get_chatroom_members")
async def get_chatroom_members(roomid: str):
    members = wcf.get_chatroom_members(roomid)
    return members


@app.get("/revoke_msg")
async def revoke_msg(id: int):
    status = wcf.revoke_msg(id)
    return status


@app.post("/send_text")
async def send_text(msg: str, receiver: str, aters: Optional[str] = ""):
    status = wcf.send_text(msg, receiver, aters)
    return status


@app.post("/send_rich_text")
async def send_rich_text(name: str, account: str, title: str, digest: str, url: str, thumburl: str, receiver: str):
    status = wcf.send_rich_text(name, account, title, digest, url, thumburl, receiver)
    return status


