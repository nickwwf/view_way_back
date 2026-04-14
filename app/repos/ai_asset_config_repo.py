# coding: utf-8
import uuid
from datetime import datetime

from app.libs.error_code import NotFound
from app.models.s_ai_asset_config import SAIAssetConfig
from app.models.base import db


class AIAssetConfigRepo:
    @staticmethod
    def create_ai_asset_config(params):
        """创建AI资产配置"""
        config = SAIAssetConfig()
        config.id = uuid.uuid4().hex
        config.ai_name = params['ai_name']
        config.price = params['price']
        config.status = params.get('status', 1)
        config.is_del = 0
        config.description = params.get('description')
        config.config_params = params.get('config_params')

        with db.auto_commit():
            db.session.add(config)
            db.session.flush()
        return config

    @staticmethod
    def get_ai_asset_config_by_id(config_id):
        """根据ID获取AI资产配置"""
        return SAIAssetConfig.query.filter_by(id=config_id, is_del=0).first()

    @staticmethod
    def get_ai_asset_config_list(page=1, size=10, filters=None):
        """获取AI资产配置列表"""
        query = SAIAssetConfig.query

        if filters:
            if 'ai_name' in filters and filters['ai_name']:
                query = query.filter(SAIAssetConfig.ai_name.like(f"%{filters['ai_name']}%"))
            if 'ai_type' in filters and filters['ai_type']:
                query = query.filter(SAIAssetConfig.ai_type == filters['ai_type'])
            if 'status' in filters and filters['status'] is not None:
                query = query.filter(SAIAssetConfig.status == filters['status'])

        pagination = query.order_by(SAIAssetConfig.created_at.desc()).paginate(
            page=page,
            per_page=size,
            error_out=False
        )

        config_list = []
        for config in pagination.items:
            config_list.append({
                'id': config.id,
                'ai_name': config.ai_name,
                'ai_type': config.ai_type,
                'model_name': config.model_name,
                'api_endpoint': config.api_endpoint,
                'api_key': config.api_key,
                'status': config.status,
                'description': config.description,
                'config_params': config.config_params,
                'created_at': config.created_at.strftime('%Y-%m-%d %H:%M:%S') if config.created_at else None,
                'updated_at': config.updated_at.strftime('%Y-%m-%d %H:%M:%S') if config.updated_at else None
            })

        return config_list, pagination.total

    @staticmethod
    def update_ai_asset_config(config_id, params):
        """更新AI资产配置"""
        config = SAIAssetConfig.query.filter_by(id=config_id).first()
        if not config:
            raise NotFound(msg="不存在此算法")

        with db.auto_commit():
            if 'ai_name' in params:
                config.ai_name = params['ai_name']
            if 'status' in params:
                config.status = params['status']
            if 'description' in params:
                config.description = params['description']
            if 'config_params' in params:
                config.config_params = params['config_params']
            if 'price' in params:
                config.config_params = params['price']
        return config

    @staticmethod
    def delete_ai_asset_config(config_id):
        """删除AI资产配置"""
        config = SAIAssetConfig.query.filter_by(id=config_id, is_del=0).first()
        if not config:
            raise NotFound(msg="不存在此AI资产配置")

        with db.auto_commit():
            config.is_del = 1
            db.session.add(config)
