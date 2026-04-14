#!/usr/bin/python
# -*- coding:utf-8 -*-
#########################################
# > File Name: sync_push_info.py
# > Author: zszaa
# > Mail: zszaa_0805@163.com
# > Created Time: 2022-07-13 14:31:41
##########################################


'''
测试案例
'''
import time

from app.models.base import db
from app.models.fs.record import BFlightRecord
from app.models.fs.b_event_type import BPushInfo
from app.libs.utils import tadd, ntime
from app.libs.redis_util import Redis
import json
from app.app import scheduler
import pandas as pd
from flask import current_app
from app.libs.ali_sms import send_msg
from app.libs.logger import logger
import requests
#import time


url = 'https://jczldn.qjq.gov.cn:8111/governanceBrain_api/pushTask/getStepBySerialNumber'
new_url = "https://jczldn.qjq.gov.cn:8111/grassrootsGovernanceBrain-prod-api/admin-api/eventCenter/getEventDetailByAlertId"
spt_url = 'http://sjzs.qz.gov.cn:8666/API_16462819566279713/sjzx/event/synch/detail'
qjdn_url = "https://jczldn.qjq.gov.cn:8111/grassrootsGovernanceBrain-prod-api/admin-api/system/auth/thirdToken"
qjdn_login = {
    "username":"drone",
    "password":"Dq3fwY*grh"
}


def demo():
    '''同步四平台信息'''
    logger.info('开始同步四平台数据！')
    query_time = tadd(h=-120)
    with scheduler.app.app_context():
        messages = BPushInfo.query.filter(
            BPushInfo.plat_name=="四平台",
            BPushInfo.status==20,
            BPushInfo.create_time>=query_time,
        ).all()
        for no,message in enumerate(messages):
            logger.info(f'[{str(no+1)}/{str(len(messages))}]:开始同步[{message.problem_code}]!')
            event_number = message.event_number
            params = {
                "appCode":"sjzxsjdjwrjxj2022@0406",
                "bizContent":{
                    "eventNumber":event_number
                }
            }
            header = {
                'Content-Type':'application/json;charset=UTF-8',
                "Connection": "close"
            }
            #req = requests.post(spt_url,headers=header,json=params,verify=False)
            #logger.info(req.json())
            time.sleep(10)
    logger.info('同步四平台数据完成！')


# 问题上报的返回状态整理
def sync_status():
    logger.info('开始同步问题的返回状态')
    query_time = tadd(h=-120)
    with scheduler.app.app_context():
        messages = BPushInfo.query.filter(
            BPushInfo.status==20,
            BPushInfo.create_time>=query_time,
        ).all()
        for no,message in enumerate(messages):
            deal_info = message.deal_info
            if message.plat_name == "衢江大脑" \
               and 'nId' in message.push_info:
                map_qjdn = {
                    8:0,61:1,1:1,63:1,21:1,
                    31:2,66:3
                }
                if deal_info:
                    data = deal_info['data'][0]
                    fs_status = map_qjdn[int(data['dealType'])]
                    message.deal_status=fs_status
                    db.session.commit()
                    logger.info(
                        f"{message.plat_name},{message.problem_code}状态:{str(fs_status)}"
                    )
            else:
                map_spt = {
                    10:0,20:1,30:1,32:1,37:1,
                    39:1,38:2,40:2,36:3
                }
                if deal_info:
                    data = deal_info['data']['eventFlowList'][0]
                    fs_status = map_spt[int(data['state'])]
                    message.deal_status = fs_status
                    db.session.commit()
                    logger.info(f"{message.plat_name},{message.problem_code}状态:{str(fs_status)}")
    return {}




