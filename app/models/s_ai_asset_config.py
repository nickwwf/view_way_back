# coding: utf-8
from sqlalchemy.dialects.mysql import TINYINT

from app.models.base import db, MixinJSONSerializer, Base


class SAIAssetConfig(Base, MixinJSONSerializer):
    __tablename__ = 'view_back_ai_asset_config'

    id = db.Column(db.String(36), primary_key=True, comment='AI资产配置主键')
    ai_name = db.Column(db.String(100), nullable=False, comment='AI名称')
    status = db.Column(db.Integer, default=1, comment='1启用 2禁用')
    is_del = db.Column(TINYINT, default=0, comment='0正常 1删除')
    price =db.Column(db.Float, default=0, comment='算法单次请求价格')
    description = db.Column(db.Text, comment='描述')
    config_params = db.Column(db.JSON, comment='配置参数')
