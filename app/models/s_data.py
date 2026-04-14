# coding: utf-8
from app.models.base import db, MixinJSONSerializer, Base


class SData(Base, MixinJSONSerializer):
    __tablename__ = 'view_back_data'

    id = db.Column(db.Integer, primary_key=True, info='数据主键')
    name = db.Column(db.String(100, 'utf8_general_ci'), nullable=False)
    type = db.Column(db.String(50, 'utf8_general_ci'))
    status = db.Column(db.String(20, 'utf8_general_ci'), default='active')
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
