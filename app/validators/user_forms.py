#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author  : Administrator
# @Time    : 2026/3/13 14:08
# @File    : user_forms.py
# @Software: PyCharm
from cgi import maxlen

from wtforms import IntegerField, FloatField, Field, StringField
from wtforms.validators import DataRequired

from app.libs.error_code import ParameterException
from app.validators.base import BaseForm


class CreateUserForm(BaseForm):
    user_name = StringField(validators=[DataRequired()])
    status = IntegerField(validators=[DataRequired()])
    balance = FloatField()
    ai_asset = Field()

    def validate_status(self, value):
        _data = value.data
        if not _data or (int(_data) not in [1, 2]):
            return ParameterException(msg="status参数无效")
        return None

    def validate_ai_asset(self, value):
        if not value or not value.data:
            self.ai_asset.data = []


class UpdateUserForm(BaseForm):
    id = StringField(validators=[DataRequired()])
    user_name = StringField(validators=[DataRequired()])
    status = IntegerField(validators=[DataRequired()])
    balance = FloatField()
    ai_asset = Field()

    def validate_status(self, value):
        _data = value.data
        if not _data or (int(_data) not in [1, 2]):
            return ParameterException(msg="status参数无效")
        return None

    def validate_ai_asset(self, value):
        if not value or not value.data:
            self.ai_asset.data = []


class DeleteUserForm(BaseForm):
    id = StringField(validators=[DataRequired()])


class UserListForm(BaseForm):
    page = IntegerField(validators=[DataRequired()], default=1)
    page_size = IntegerField(validators=[DataRequired()], default=20)
    search = StringField()
    status = IntegerField()
