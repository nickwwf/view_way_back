# coding: utf-8
import uuid
from sqlalchemy import JSON
from app.models.base import db, MixinJSONSerializer, Base


class SRecognitionNode(Base, MixinJSONSerializer):
    __tablename__ = 'view_back_recognition_node'

    id = db.Column(db.String(36), default=lambda: uuid.uuid4().hex, primary_key=True, comment='主键ID(UUID)')
    recognition_id = db.Column(db.String(36), nullable=False, comment='识别结果ID')
    node_type = db.Column(db.String(50, 'utf8_general_ci'), nullable=False, comment='节点类型 待识别(waiting)、识别中(processing)、识别完成(success)、识别失败(fail)、成果已输出(output)')
    node_info = db.Column(JSON, default={}, comment='节点信息(JSON数据)')
