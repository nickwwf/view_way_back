# coding: utf-8
import uuid

from app.models.base import db, MixinJSONSerializer, Base


class SConsumption(Base, MixinJSONSerializer):
    __tablename__ = 'view_back_consumption'

    id = db.Column(db.String(36), primary_key=True, default=lambda: uuid.uuid4().hex, info='消费记录主键')
    user_id = db.Column(db.String(36), nullable=False, info='用户ID')
    recognition_id = db.Column(db.String(36), nullable=False, info='识别结果ID')
    amount = db.Column(db.Float, nullable=False, info='消费金额')
    consumption_type = db.Column(db.String(50, 'utf8_general_ci'), default='image_recognition', info='消费类型')
    description = db.Column(db.String(200, 'utf8_general_ci'), info='消费描述')
    status = db.Column(db.String(20, 'utf8_general_ci'), default='completed', info='状态 pre预扣除 down已扣除 back已返还')
