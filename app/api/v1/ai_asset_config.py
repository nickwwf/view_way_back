# coding: utf-8
from flask import request, g

from app.libs.define_print import DefinePrint
from app.libs.error_code import Success, ServerError, NotFound
from app.libs.helper import iPagenation
from app.libs.token_auth import login_required
from app.models.base import db
from app.models.s_ai_asset_config import SAIAssetConfig
from app.repos.ai_asset_config_repo import AIAssetConfigRepo
from app.validators.ai_asset_config_forms import CreateAIAssetConfigForm, UpdateAIAssetConfigForm, DeleteAIAssetConfigForm, AIAssetConfigListForm

api = DefinePrint('ai_asset_config')


@api.route('/create', methods=['POST'])
@login_required
def create_ai_asset_config():
    """创建AI资产配置"""
    form = CreateAIAssetConfigForm().validate_for_api()
    if g.user_id != "view_way_admin_2026":  # 判断是不是管理员
        return Success(msg="无权限")
    config = AIAssetConfigRepo.create_ai_asset_config(form.data)
    return Success(data={
        'id': config.id,
        'ai_name': config.ai_name
    })


@api.route('/update', methods=['POST'])
@login_required
def update_ai_asset_config():
    """更新AI资产配置"""
    form = UpdateAIAssetConfigForm().validate_for_api()
    if g.user_id != "view_way_admin_2026":  # 判断是不是管理员
        return Success(msg="无权限")
    AIAssetConfigRepo.update_ai_asset_config(form.id.data, form.data)
    return Success()


@api.route('/delete', methods=['POST'])
@login_required
def delete_ai_asset_config():
    """删除AI资产配置"""
    form = DeleteAIAssetConfigForm().validate_for_api()
    if g.user_id != "view_way_admin_2026":  # 判断是不是管理员
        return Success(msg="无权限")
    AIAssetConfigRepo.delete_ai_asset_config(form.id.data)
    return Success()


@api.route('/info', methods=['GET'])
@login_required
def get_ai_asset_config_info():
    """获取AI资产配置详情"""
    config_id = request.args.get('id')
    if not config_id:
        return ServerError(msg='Config ID is required')
    if g.user_id != "view_way_admin_2026":  # 判断是不是管理员
        return Success(msg="无权限")
    config = AIAssetConfigRepo.get_ai_asset_config_by_id(config_id)
    if not config:
        return NotFound(msg='AI asset config not found')

    return Success(data={
        'id': config.id,
        'ai_name': config.ai_name,
        'status': config.status,
        'price': config.price,
        'description': config.description,
        'config_params': config.config_params,
        'create_time': config.create_time.strftime('%Y-%m-%d %H:%M:%S') if config.create_time else None,
        'update_time': config.update_time.strftime('%Y-%m-%d %H:%M:%S') if config.update_time else None
    })


@api.route('/list', methods=['GET'])
@login_required
def get_ai_asset_config_list():
    """获取AI资产配置列表"""
    form = AIAssetConfigListForm().validate_for_api()
    if g.user_id != "view_way_admin_2026":  # 判断是不是管理员
        return Success(msg="无权限")
    page = form.page.data
    page_size = form.page_size.data
    
    filters = []
    if form.search.data:
        filters.append(SAIAssetConfig.ai_name.like(f"%{form.search.data}%"))
    filters.append(SAIAssetConfig.is_del == 0)
    
    query = db.session.query(SAIAssetConfig).filter(*filters).order_by(SAIAssetConfig.create_time.desc())
    configs = query.paginate(page=page, per_page=page_size, error_out=False)
    data = iPagenation(configs)
    _items = []
    for item in data['items']:
        _items.append({
            'id': item['id'],
            'ai_name': item['ai_name'],
            'status': item['status'],
            'price': item['price'],
            'description': item['description'],
            'config_params': item['config_params'],
            'create_time': item['create_time'].strftime('%Y-%m-%d %H:%M:%S') if item['create_time'] else None
        })
    data['items'] = _items
    return Success(data=data)


@api.route('/algorithm_list', methods=['GET'])
@login_required
def get_algorithm_list():
    """获取开启的算法列表"""
    configs = SAIAssetConfig.query.filter(SAIAssetConfig.status == 1, SAIAssetConfig.is_del == 0).all()
    items = []
    for config in configs:
        items.append({
            'id': config.id,
            'ai_name': config.ai_name,
            'price': config.price,
            'description': config.description,
            'config_params': config.config_params
        })
    return Success(data=items)
    
