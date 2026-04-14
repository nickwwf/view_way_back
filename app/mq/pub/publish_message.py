#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author  : Administrator
# @Time    : 2026/4/7 14:20
# @File    : publish_message.py
# @Software: PyCharm

"""
向mq发送消息
"""
import datetime
import json

from app import rabbit
from app.libs.utils import get_second_format, NpEncoder


def publish_detect(body: dict):
    body.update({"time": datetime.datetime.now().strftime(get_second_format())})
    rabbit.send('img_detect', 'img_detect', 'img_detect', json.dumps(body, cls=NpEncoder), deal_dead_letter=True)
    # 待识别、识别中、识别完成(成功or失败)、成果已输出
    """
    {
        "time": "2026-04-01 09:00:00",
        "image_url": "",
        "bus_id": "",
        "topic": "begin_detect"
    }
    """
    
class SendMQ(object):

    @staticmethod
    def publish_begin_detect(_msg):
        _msg.update({"topic": "begin_detect"})
        publish_detect(_msg)
