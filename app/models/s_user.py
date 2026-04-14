# coding: utf-8
import uuid

from sqlalchemy import JSON
from sqlalchemy.dialects.mysql import TINYINT

from app.models.base import db, MixinJSONSerializer, Base


class SUser(Base, MixinJSONSerializer):
    __tablename__ = 'view_back_user'
    id = db.Column(db.String(36), default=lambda: uuid.uuid4().hex, primary_key=True, comment='用户主键')
    user_name = db.Column(db.String(50), comment='用户名')
    status = db.Column(TINYINT, default=1, comment='1开启 2关闭,关闭后账户失效无法登录')
    balance = db.Column(db.Float, default=0.0, comment='账号余额')
    ai_asset = db.Column(JSON, default=[], comment='配置的AI资产')
    app_key = db.Column(db.String(50, 'utf8_general_ci'), nullable=False, unique=True)
    app_secret = db.Column(db.String(50, 'utf8_general_ci'))
    callback_url = db.Column(db.String(255, 'utf8_general_ci'), comment='回调地址')
    callback_enabled = db.Column(TINYINT, default=2, comment='1开启 2关闭,关闭后回调地址无效')
    callback_token = db.Column(db.String(255, 'utf8_general_ci'), comment='回调鉴权Token(用于回调接口鉴权)')
