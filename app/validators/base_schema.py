#!/usr/bin/python
# -*- coding:utf-8 -*-

from app.validators import *
from marshmallow import Schema, validates, ValidationError, INCLUDE
from .error_msg import ErrorMsg
import re


class SchemaBase(Schema):
    class Meta:
        unknown = INCLUDE


class PhoneSchema(Schema):
    phone = String(required=True, error_messages=ErrorMsg.tel_null)

    @validates('phone')
    def validate_phone(self, value):
        if not re.match(r"^1[3-9]\d{9}$", value):
            raise ValidationError('手机号格式不正确!')

class TelSchema(Schema):
    tel = String(required=True, error_messages=ErrorMsg.tel_null)

    @validates('tel')
    def validate_tel(self, value):
        if not re.match(r"^1[3-9]\d{9}$", value):
            raise ValidationError('手机号格式不正确!')
