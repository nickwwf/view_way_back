from datetime import date
from decimal import Decimal
from flask import Flask as _Flask
from flask.json import JSONEncoder as _JSONEncoder

from app.libs.error_code import ServerError

from flask_apscheduler import APScheduler as _BaseAPScheduler
from app.plug.rabbit import RabbitMq
from app.plug.mqtt import Mqtt
from app.plug.fsee_log import FseeLogs

class JSONEncoder(_JSONEncoder):
    def default(self, o):
        if hasattr(o, 'keys') and hasattr(o, '__getitem__'):
            return dict(o)
        if isinstance(o, date):
            return o.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(o, Decimal):
            return float(o)
        raise ServerError()


class Flask(_Flask):
    json_encoder = JSONEncoder


class APScheduler(_BaseAPScheduler):
    def run_job(self, id, jobstore=None):
        with self.app.app_context():
            super().run_job(id=id, jobstore=jobstore)

scheduler = APScheduler()
rabbit = RabbitMq()

# TODO 整合mqtt
dji_mqtt = Mqtt()
test_mqtt = Mqtt()
zk1_mqtt = Mqtt()

# log
flogs = FseeLogs()