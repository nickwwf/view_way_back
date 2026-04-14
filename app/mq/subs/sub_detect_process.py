#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author  : Administrator
# @Time    : 2026/4/7 14:42
# @File    : sub_detect_process.py
# @Software: PyCharm

"""
监听识别进度
"""
import json
import sys
import threading
from time import sleep
import datetime
from app.libs.utils import get_second_format

import requests

from app.libs.db_session_factory import db_factory
from app.libs.logger import logger_mq
from app.mq.subs.sub_base import SubBase
from app.models.s_recognition_node import SRecognitionNode
from app.models.s_recognition_result import SRecognitionResult
from app.models.s_user import SUser
from app.repos.consumption_repo import ConsumptionRepo


class SubDetectProcess(SubBase):

    def __init__(self):
        super().__init__()
        self.queue = "detect_process"

    def callback(self, channel, method, properties, body):
        data = json.loads(body.decode())
        try:
            if method.routing_key == 'detect_process':
                if data:
                    topic = data.get('topic', "")
                    bus_id = data.get('bus_id', "")
                    detect_data = data.get('detect_data', {})  # 识别服务输出数据
                    if topic == "detecting":
                        self.detecting_node(bus_id, detect_data)
                    elif topic == "detect_success":
                        self.detect_success_node(bus_id, detect_data)
                    elif topic == "detect_fail":
                        self.detect_fail_node(bus_id, detect_data)
                channel.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger_mq.error(f'监听detect_process报错 {str(e)}, {json.dumps(data)}')

    def detecting_node(self, bus_id, detect_data):
        session = db_factory.get_session()
        try:
            recognition = session.query(SRecognitionResult).filter_by(id=bus_id).first()
            if recognition:
                node = SRecognitionNode()
                node.recognition_id = recognition.id
                node.node_type = 'processing'
                node.node_info = detect_data
                session.add(node)
                recognition.status = 'processing'
                session.add(recognition)
            session.commit()
        except Exception as ex:
            session.rollback()
            raise ex
        finally:
            db_factory.close_session(session)

    def detect_success_node(self, bus_id, detect_data):
        session = db_factory.get_session()
        try:
            recognition = session.query(SRecognitionResult).filter_by(id=bus_id).first()
            if recognition:
                # 判断用户是否配置了回调地址
                user = session.query(SUser).filter_by(id=recognition.user_id).first()
                node_type = 'success'
                if user and user.callback_url and int(getattr(user, 'callback_enabled', 1) or 1) == 1:
                    try:
                        headers = {}
                        token = (getattr(user, 'callback_token', None) or '').strip()
                        if token:
                            headers['Authorization'] = f'Bearer {token}'
                            headers['X-Callback-Token'] = token
                        requests.post(
                            user.callback_url,
                            json={'bus_id': bus_id, 'time': datetime.datetime.now().strftime(get_second_format()), 'detect_data': detect_data},
                            headers=headers,
                            timeout=8
                        )
                        node_type = 'output'
                    except Exception as e:
                        logger_mq.error(f"调用回调地址失败: {str(e)}")
                node = SRecognitionNode()
                node.recognition_id = recognition.id
                node.node_type = node_type
                node.node_info = detect_data
                session.add(node)
                recognition.status = node_type
                recognition.recognition_result = detect_data  # TODO 这里和算法服务对接时写入识别结果
                session.add(recognition)
                ConsumptionRepo.mark_down(bus_id, session=session, auto_commit=False)
            session.commit()
        except Exception as ex:
            session.rollback()
            raise ex
        finally:
            db_factory.close_session(session)

    def detect_fail_node(self, bus_id, detect_data):
        session = db_factory.get_session()
        try:
            recognition = session.query(SRecognitionResult).filter_by(id=bus_id).first()
            if recognition:
                node = SRecognitionNode()
                node.recognition_id = recognition.id
                node.node_type = 'fail'
                node.node_info = detect_data
                session.add(node)
                recognition.status = 'fail'
                session.add(recognition)
                ConsumptionRepo.mark_back(bus_id, session=session, auto_commit=False)
            session.commit()
        except Exception as ex:
            session.rollback()
            raise ex
        finally:
            db_factory.close_session(session)


class MonitorDetectProcess(threading.Thread):

    def __init__(self, daemon=None):
        threading.Thread.__init__(self, daemon=daemon)

    def run(self):
        # monitor
        sleep(5)
        sub = SubDetectProcess()
        sub.subscribe()


if __name__ == "__main__":  # 这里可以改为使用supervisord托管启动
    try:
        logger_mq.info("SubDetectProcess进程启动")
        sub = SubDetectProcess()
        sub.subscribe()
    except Exception as ex:
        logger_mq.error(f"SubDetectProcess异常退出:{ex}")
        sys.exit()
