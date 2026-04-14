#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from wtforms import IntegerField, Field, StringField
from wtforms.fields.numeric import FloatField
from wtforms.validators import DataRequired

from app.libs.error_code import ParameterException
from app.validators.base import BaseForm


class CreateAIAssetConfigForm(BaseForm):
    ai_name = StringField(validators=[DataRequired()])
    price = FloatField()
    status = IntegerField()
    description = StringField()
    config_params = Field()

    def validate_status(self, value):
        _data = value.data
        if _data is not None and (int(_data) not in [1, 2]):
            raise ParameterException(msg="status参数无效，1表示启用，2表示禁用")
        return None

    def validate_config_params(self, value):
        if not value or not value.data:
            self.config_params.data = {}


class UpdateAIAssetConfigForm(BaseForm):
    id = StringField(validators=[DataRequired()])
    ai_name = StringField(validators=[DataRequired()])
    price = FloatField()
    status = IntegerField()
    description = StringField()
    config_params = Field()

    def validate_status(self, value):
        _data = value.data
        if _data is not None and (int(_data) not in [1, 2]):
            raise ParameterException(msg="status参数无效，1表示启用，2表示禁用")
        return None

    def validate_config_params(self, value):
        if not value or not value.data:
            self.config_params.data = {}


class DeleteAIAssetConfigForm(BaseForm):
    id = StringField(validators=[DataRequired()])


class AIAssetConfigListForm(BaseForm):
    page = IntegerField(validators=[DataRequired()], default=1)
    page_size = IntegerField(validators=[DataRequired()], default=20)
    search = StringField()
