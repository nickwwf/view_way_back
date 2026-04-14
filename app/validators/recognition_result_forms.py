# coding: utf-8
from wtforms import StringField, IntegerField, Field
from wtforms.validators import DataRequired

from app.validators.base import BaseForm


class CreateRecognitionResultForm(BaseForm):
    image_urls = Field(validators=[DataRequired()])
    algorithm_type = StringField(validators=[DataRequired()])
    detect_alg = Field(validators=[DataRequired()])


class UpdateRecognitionResultForm(BaseForm):
    id = StringField(validators=[DataRequired()])
    algorithm_type = StringField()
    recognition_result = StringField()


class RecognitionResultListForm(BaseForm):
    page = IntegerField(validators=[DataRequired()], default=1)
    page_size = IntegerField(validators=[DataRequired()], default=20)
    search = StringField()
    status = StringField()
