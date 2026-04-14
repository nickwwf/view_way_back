from datetime import date
from decimal import Decimal

from flask import Flask as _Flask
from flask.json import JSONEncoder as _JSONEncoder

from app.libs.error_code import ServerError
from app.plug.rabbit import RabbitMq


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

rabbit = RabbitMq()
