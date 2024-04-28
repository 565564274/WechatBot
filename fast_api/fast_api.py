# -*- encoding:utf-8 -*-
import logging
import xml.etree.ElementTree as ET
import threading
import pprint

from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, Request, HTTPException, Query, status
from fastapi.staticfiles import StaticFiles
from wcferry import Wcf

from utils import resource_pool
from utils.log import logger_manager
from fast_api.statics.static_api import static_app
from Bot.robot import Robot


logger = logger_manager.logger
app = FastAPI(docs_url=None, redoc_url=None)
static_dir = Path(__file__).parents[0] / "statics"
app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.include_router(static_app.router, prefix="", tags=[])
wcf = Wcf(debug=True)


@app.on_event("startup")
async def startup_event():
    robot = Robot(resource_pool, wcf)
    robot.LOG.info(f"WeChatRobot成功启动···")

    # 机器人启动发送测试消息
    robot.sendTextMsg("机器人启动成功！", "filehelper")

    # 接收消息
    robot.enableReceivingMsg()  # 加队列

    # 每天 7 点发送天气预报
    # robot.onEveryTime("07:00", weather_report, robot=robot)

    # 每天 7:30 发送新闻
    # robot.onEveryTime("07:30", robot.newsReport)

    # 每天 16:30 提醒发日报周报月报
    # robot.onEveryTime("16:30", ReportReminder.remind, robot=robot)

    # 让机器人一直跑
    robot.keepRunningAndBlockProcess()



@app.on_event('shutdown')
async def shutdown_event():
    wcf.cleanup()  # 退出前清理环境


# @app.post("/send", response_model=NormalResponse)
# async def send():
#     dte_manager = await create_send()
#     return NormalResponse(data="success")


@app.post("/sync_messages")
async def sync_messages(userid: str, messages: dict = None, return_data: bool = False):
    if userid != verify_userid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect userid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    massage_job = MessageHistory()
    global qy_kf_custom
    with lock:
        if messages:
            qy_kf_custom = massage_job.sync(messages)
        else:
            qy_kf_custom = massage_job.sync(qy_kf_custom)
    return qy_kf_custom if return_data else ""



