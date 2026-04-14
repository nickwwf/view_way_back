#!/usr/bin/env python
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

import traceback
import pika

from app.env import load_conf

rabbit_host = load_conf.get('RABBIT_HOST')
rabbit_port = load_conf.get('RABBIT_PORT')
rabbit_username = load_conf.get('RABBIT_USERNAME')
rabbit_passwd = load_conf.get('RABBIT_PASSWD')


class SubBase:
    def __init__(self):
        self.host = rabbit_host
        self.port = rabbit_port
        self.auth = pika.PlainCredentials(rabbit_username, rabbit_passwd)

        self.queue = ""

    def connect(self):
        return pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.host, port=self.port,
                virtual_host='/', credentials=self.auth, heartbeat=600, blocked_connection_timeout=300,
                connection_attempts=3,
                retry_delay=5
            )
        )

    def subscribe(self):
        conn = self.connect()
        channel = conn.channel()
        channel.basic_qos(prefetch_count=10)
        channel.queue_declare(queue=self.queue, durable=True)
        channel.basic_consume(
            queue=self.queue, on_message_callback=self._callback
        )
        try:
            channel.start_consuming()
        except Exception as e:
            channel.stop_consuming()
            raise Exception(f"停止消费队列{self.queue}:{traceback.format_exc()}")
        finally:
            self._clean_up(conn, channel)

    def _callback(self, channel, method, properties, body):
        try:
            self.callback(channel, method, properties, body)
        except Exception as e:
            raise Exception()

    def callback(self, channel, method, properties, body):
        raise Exception("未实现监听逻辑")

    def _clean_up(self, connection, channel):
        try:
            if channel and channel.is_open:
                channel.close()
            if connection and connection.is_open:
                connection.close()
        except Exception as e:
            raise Exception(f"清理资源时出错: {traceback.format_exc()}")
