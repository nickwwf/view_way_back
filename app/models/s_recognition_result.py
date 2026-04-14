# coding: utf-8
import uuid
from sqlalchemy import JSON
from sqlalchemy.dialects.mysql import TINYINT
from app.models.base import db, MixinJSONSerializer, Base


class SRecognitionResult(Base, MixinJSONSerializer):
    __tablename__ = 'view_back_recognition_result'

    id = db.Column(db.String(36), default=lambda: uuid.uuid4().hex, primary_key=True, comment='主键ID(UUID)')
    image_no = db.Column(db.String(50), nullable=False, comment='图片编号')
    image_url = db.Column(db.String(500, 'utf8_general_ci'), nullable=False, comment='图片地址')
    thumbnail_url = db.Column(db.String(500, 'utf8_general_ci'), nullable=True, comment='缩略图地址')
    user_id = db.Column(db.String(36), db.ForeignKey('view_back_user.id'), nullable=False, comment='用户ID')
    algorithm_type = db.Column(db.String(50, 'utf8_general_ci'), nullable=False, comment='识别模式')
    status = db.Column(db.String(20, 'utf8_general_ci'), default='waiting', comment='识别状态(与node_type同步)')
    recognition_result = db.Column(JSON, default={}, comment='识别结果(JSON数据)')
    detect_alg = db.Column(JSON, default=[], comment='检测算法')
