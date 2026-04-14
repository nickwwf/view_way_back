#!/usr/bin/python
# -*- coding:utf-8 -*-

import json
import threading
from functools import wraps

import pika
from pika.exchange_type import ExchangeType
from retry import retry

from app.libs.logger import logger_rabbit
from app.plug.rabbit.utils import AMQPConnectionError

'''
1. 默认使用direct模式
2. 默认使用持久化队列
'''

class RabbitMq(object):

    def __init__(self, app=None):
        # TODO exchange_type
        self.consumers = set()
        self.middlewares = None
        self.username = None
        self.passwd = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        self.check_config()
        self.config = self.app.config
        self.host = self.app.config['RABBIT_HOST']
        self.port = self.app.config['RABBIT_PORT']
        self.username = self.app.config['RABBIT_USERNAME']
        self.passwd = self.app.config['RABBIT_PASSWD']
        self._channel = self._connect.channel()
        # excute callback
        for consumer in self.consumers:
            consumer()

    def check_config(self):
        # TODO check config
        return True

    @property
    def _connect(self):
        # rabbitmq 默认为单线程
        # 每个线程都有自己的channel,创建queue之前必须新建connect
        if not (self.username and self.passwd):
            connect = pika.BlockingConnection()
        elif self.username and self.passwd:
            _credentials = pika.PlainCredentials(self.username, self.passwd)
            connect = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=self.host, port=self.port, credentials=_credentials,
                    # heartbeat=0
                    heartbeat=600, blocked_connection_timeout=300
                )
            )
        else:
            raise Exception('rabbitmq config error')
        return connect

    def queue_declare(self, channel, queue_name='', durable=True, arguments=None):
        '''declare queue
        :param queue_name: queue name
        '''
        # TODO auto_delete,exclusive...
        channel.queue_declare(
            queue=queue_name, durable=durable, arguments=arguments
        )

    def bind_queue(self, channel, queue_name, exchange, routing_key):
        '''bind queue
        :param queue_name: queue name
        :param exchange: exchange name
        :param routing_key: routing key
        '''
        channel.queue_bind(
            queue=queue_name, exchange=exchange, routing_key=routing_key,
        )

    def send(self, exchange, routing_key, queue_name, body, durable=True, deal_dead_letter=False):
        '''publish message
        :param exchange: exchange name
        '''
        # TODO 目前常用为direct模式，后续可扩展
        __channel = self._connect.channel()
        if exchange:
            __channel.exchange_declare(
                exchange=exchange, exchange_type=ExchangeType.direct,
                durable=durable,
            )
        if deal_dead_letter:
            dead_letter_exchange = f"dead_letter_{exchange}" if exchange else "dead_letter_default"
            dead_letter_queue = f"dead_letter_{queue_name}"
            __channel.exchange_declare(exchange=dead_letter_exchange, exchange_type=ExchangeType.direct)
            __channel.queue_declare(queue=dead_letter_queue, durable=durable)
            # 为死信队列设置绑定
            __channel.queue_bind(exchange=dead_letter_exchange, queue=dead_letter_queue, routing_key=routing_key)

            self.queue_declare(__channel, queue_name=queue_name, durable=durable, arguments={
                'x-dead-letter-exchange': dead_letter_exchange,
                'x-dead-letter-routing-key': routing_key
            })
        else:
            self.queue_declare(__channel, queue_name=queue_name, durable=durable)

        if exchange and queue_name and routing_key:
            self.bind_queue(__channel, queue_name, exchange, routing_key)
        if durable:
            __channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=body,
                properties=pika.BasicProperties(
                    content_type='text/plain',
                    delivery_mode=pika.DeliveryMode.Persistent,  # make message persistent
                )
            )
        else:
            __channel.basic_publish(
                exchange=exchange, routing_key=routing_key,
                body=body,
            )

    def publish(self, queue, exchange, routing_key, body):
        '''
        :param queue: 队列名称
        :param exchange: 交换机名称,默认为''
        :param routing_key: 等于queue
        :param body: 消息内容s
        :return:
        '''
        # 发布消息
        conn = self._connect
        channel = conn.channel()
        # 持久化
        channel.queue_declare(queue=queue, durable=True)
        channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=body,
            properties=pika.BasicProperties(
                content_type='text/plain',
                delivery_mode=2
            )
        )

    def queue(
            self, exchange, route_key, queue_name='',
            persistent=True, exchange_type=ExchangeType.direct,
            auto_ack=True, deal_dead_letter=False
    ):
        """queue decorator
        :param persistent: if True,queue is durable
        """

        def decorator(func):
            @wraps(func)
            def new_consumer(*args, **kwargs):
                return self._setup_connection(
                    func, exchange, route_key, queue_name, auto_ack, deal_dead_letter
                )
                return None

            # adds consumers
            if self.app is not None:
                new_consumer()
            else:
                self.consumers.add(new_consumer)
            return func

        return decorator

    def _setup_connection(
            self, func, exchange, route_key,
            queue_name, auto_ack, deal_dead_letter
    ):
        def create_queue():
            return self._add_exchange_queue(
                func, exchange, route_key, queue_name, auto_ack, deal_dead_letter
            )

        thread = threading.Thread(
            target=create_queue, name=func.__name__
        )
        thread.daemon = True
        thread.start()

    @retry((AMQPConnectionError, AssertionError), delay=2, jitter=(5, 15))
    def _add_exchange_queue(self, func, exchange, route_key, queue_name, auto_ack, deal_dead_letter):
        # TODO 是否只需要给定queue_name即可？
        conn = self._connect
        channel = conn.channel()
        # Declare exchange
        channel.exchange_declare(
            exchange=exchange, exchange_type=ExchangeType.direct,
            durable=True, auto_delete=False,
        )
        # Declare queue
        if deal_dead_letter:
            dead_letter_exchange = f"dead_letter_{exchange}" if exchange else "dead_letter_default"
            dead_letter_queue = f"dead_letter_{queue_name}"
            channel.exchange_declare(exchange=dead_letter_exchange, exchange_type=ExchangeType.direct)
            channel.queue_declare(queue=dead_letter_queue, durable=True)
            # 为死信队列设置绑定
            channel.queue_bind(exchange=dead_letter_exchange, queue=dead_letter_queue, routing_key=route_key)

            channel.queue_declare(queue=queue_name, durable=True, arguments={
                'x-dead-letter-exchange': dead_letter_exchange,
                'x-dead-letter-routing-key': route_key
            })
        else:
            channel.queue_declare(queue=queue_name, durable=True)

        def call_back(ch, method, properties, body):
            with self.app.app_context():
                null = None
                false = False
                true = True
                if body == b'':
                    pass
                else:
                    try:
                        res = eval(body.decode())
                        exe_res = func(res)  # 加个返回结果判断
                        if (not exe_res) or (exe_res == 'suc'):
                            ch.basic_ack(delivery_tag=method.delivery_tag)
                        elif exe_res == 'fail':
                            logger_rabbit.error(f'{exe_res}:{body}')
                            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
                    except Exception as ex:
                        logger_rabbit.error(f'{ex}:{body}')
                        ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)

        channel.basic_qos(prefetch_size=0, prefetch_count=1)
        channel.basic_consume(
            queue=queue_name, on_message_callback=call_back, auto_ack=auto_ack
        )
        channel.start_consuming()

    def _close(self):
        self._connect.close()

    def publish_topic(self, queue, body):
        # 判断body是否为json
        if isinstance(body, dict):
            body = json.dumps(body)
        self.send("", queue, queue, body)

    def publish_msg_list(self, queue_list, body):
        for queue in queue_list:
            self.publish_topic(queue, body)
            logger_rabbit.info(f"publish_topic:{queue},{body}")
