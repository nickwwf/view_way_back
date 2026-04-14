# coding: utf-8
import datetime

import requests
from flask import request, g
from sqlalchemy import or_

from app.libs.define_print import DefinePrint
from app.libs.error_code import Success, ServerError, AuthFailed, NotFound, TokenFailed
from app.libs.helper import iPagenation
from app.libs.token_auth import login_required, generate_token_pair, generate_access_token, verify_refresh_token
from app.libs.utils import get_second_format
from app.models import SUser
from app.models.base import db
from app.models.s_ai_asset_config import SAIAssetConfig
from app.repos.user_repo import UserRepo
from app.validators.user_forms import CreateUserForm, UpdateUserForm, DeleteUserForm, UserListForm

api = DefinePrint('user')


@api.route('/create', methods=['POST'])
@login_required
def create_user():
    form = CreateUserForm().validate_for_api()
    if g.user_id != "view_way_admin_2026":  # 判断是不是管理员
        return Success(msg="无权限")
    user = UserRepo.create_user(form.data)
    return Success(data={
        'app_key': user.app_key,
        'app_secret': user.app_secret
    })


@api.route('/update', methods=['POST'])
@login_required
def update_user():
    form = UpdateUserForm().validate_for_api()
    if g.user_id != "view_way_admin_2026":  # 判断是不是管理员
        return Success(msg="无权限")
    UserRepo.update_user(form.id.data, form.data)
    return Success()


@api.route('/delete', methods=['POST'])
@login_required
def delete_user():
    form = DeleteUserForm().validate_for_api()
    if g.user_id != "view_way_admin_2026":  # 判断是不是管理员
        return Success(msg="无权限")
    UserRepo.delete_user(form.id.data)
    return Success()



@api.route('/info', methods=['GET'])
@login_required
def get_user_info():
    user_id = request.args.get('id')
    if not user_id:
        return ServerError(msg='User ID is required')
    if g.user_id != "view_way_admin_2026":
        return Success(msg="无权限")
    user = UserRepo.get_user_by_id(user_id)
    if not user:
        return NotFound(msg='User not found')

    valid_ai_assets = []
    if user.ai_asset:
        valid_configs = SAIAssetConfig.query.filter(
            SAIAssetConfig.id.in_(user.ai_asset),
            SAIAssetConfig.status == 1,
            SAIAssetConfig.is_del == 0
        ).all()
        valid_ids = {c.id for c in valid_configs}
        valid_ai_assets = [aid for aid in user.ai_asset if aid in valid_ids]

    return Success(data={
        'id': user.id,
        'user_name': user.user_name,
        'status': user.status,
        'balance': user.balance,
        'ai_asset': valid_ai_assets,
        'app_key': user.app_key,
        'app_secret': user.app_secret,
        'create_time': user.create_time.strftime('%Y-%m-%d %H:%M:%S') if user.create_time else None
    })


@api.route('/list', methods=['GET'])
@login_required
def get_user_list():
    form = UserListForm().validate_for_api()
    if g.user_id != "view_way_admin_2026":  # 判断是不是管理员
        return Success(msg="无权限")
    page = form.page.data
    page_size = form.page_size.data
    filters = []
    if form.search.data:
        filters.append(or_(SUser.user_name.like(f"%{form.search.data}%"), SUser.app_key.like(f"%{form.search.data}%")))
    if form.status.data:
        filters.append(SUser.status == form.status.data)
    query = db.session.query(SUser).filter(*filters).order_by(SUser.create_time.desc())
    users = query.paginate(page=page, per_page=page_size, error_out=False)
    data = iPagenation(users)

    enabled_configs = {c.id: c.ai_name for c in SAIAssetConfig.query.filter(SAIAssetConfig.status == 1, SAIAssetConfig.is_del == 0).all()}

    _items = []
    for item in data['items']:
        ai_asset_names = []
        if item['ai_asset']:
            for asset_id in item['ai_asset']:
                if asset_id in enabled_configs:
                    ai_asset_names.append(enabled_configs[asset_id])
        _items.append({
            'id': item['id'],
            'user_name': item['user_name'],
            'status': item['status'],
            'balance': item['balance'],
            'ai_asset': ai_asset_names,
            'app_key': item['app_key'],
            'app_secret': item['app_secret'],
            'create_time': item['create_time'].strftime('%Y-%m-%d %H:%M:%S') if item['create_time'] else None
        })
    data['items'] = _items
    return Success(data=data)


@api.route('/login', methods=['POST'])
def login():
    """用户登录接口
    
    流程：
    1. 接收账号密码
    2. 查询用户信息
    3. 验证密码
    4. 生成Access Token(15分钟)和Refresh Token(7天)
    5. 返回Tokens
    """
    data = request.json
    if not data or 'app_key' not in data or 'app_secret' not in data:
        return ServerError(msg='App key and app secret are required')

    app_key = data['app_key']
    app_secret = data['app_secret']

    # 2. 查询用户信息
    user = UserRepo.get_user_by_app_key(app_key)
    if not user:
        return AuthFailed(msg='Invalid app key or app secret')

    # 3. 验证密码
    if user.app_secret != app_secret:
        return AuthFailed(msg='Invalid app key or app secret')

    # 4. 生成Access Token和Refresh Token
    token_pair = generate_token_pair(user.id, 'user')

    # 获取权限菜单
    auth_menu = [""]
    if user.id == "view_way_admin_2026":  # 管理员
        auth_menu = ["accounts", "algorithms"]

    # 5. 返回Tokens
    return Success(data={
        'access_token': token_pair['access_token'],
        'refresh_token': token_pair['refresh_token'],
        'user_name': user.user_name,
        'auth_menu': auth_menu
    })


@api.route('/callback_config', methods=['GET'])
@login_required
def get_callback_config():
    user_id = g.user_id
    user = SUser.query.filter_by(id=user_id).first()
    if not user:
        return NotFound(msg='User not found')
    return Success(data={
        'callback_url': user.callback_url or '',
        'callback_enabled': int(getattr(user, 'callback_enabled', 1) or 1),
        'callback_token': (getattr(user, 'callback_token', None) or '')
    })


@api.route('/callback_config/update', methods=['POST'])
@login_required
def update_callback_config():
    data = request.json or {}
    callback_url = (data.get('callback_url') or data.get('url') or '').strip()
    callback_enabled = data.get('callback_enabled')
    callback_token = (data.get('callback_token') or '').strip()
    user_id = g.user_id

    enabled_flag = 1 if int(callback_enabled or 0) == 1 else 2
    if enabled_flag == 1:
        if not callback_url:
            return ServerError(msg='Callback url is required')
        if not callback_url.lower().startswith(('http://', 'https://')):
            return ServerError(msg='Callback url must start with http:// or https://')
        payload = {
            'bus_id': 'test_save_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
            'time': datetime.datetime.now().strftime(get_second_format()),
            'detect_data': {
                'topic': 'test_callback',
                'note': 'save_validation'
            }
        }
        try:
            headers = {}
            if callback_token:
                headers['Authorization'] = f'Bearer {callback_token}'
                headers['X-Callback-Token'] = callback_token
            resp = requests.post(callback_url, json=payload, headers=headers, timeout=8)
            if resp.status_code < 200 or resp.status_code >= 300:
                return ServerError(msg=f'Callback test failed: HTTP {resp.status_code}')
        except Exception as e:
            return ServerError(msg=f'Callback test failed: {str(e)}')

    with db.auto_commit():
        user = db.session.query(SUser).filter_by(id=user_id).with_for_update().first()
        if not user:
            return NotFound(msg='User not found')
        user.callback_url = callback_url
        if callback_enabled is not None:
            user.callback_enabled = enabled_flag
        user.callback_token = callback_token
        db.session.add(user)
    return Success(data={
        'callback_url': callback_url,
        'callback_enabled': int(getattr(user, 'callback_enabled', 1) or 1),
        'callback_token': (getattr(user, 'callback_token', None) or '')
    })


@api.route('/callback_config/test', methods=['POST'])
@login_required
def test_callback_config():
    data = request.json or {}
    callback_url = (data.get('callback_url') or data.get('url') or '').strip()
    bus_id = (data.get('bus_id') or '').strip()
    detect_data = data.get('detect_data')
    callback_token = (data.get('callback_token') or '').strip()

    user = None
    if not callback_url:
        user = SUser.query.filter_by(id=g.user_id).first()
        callback_url = (user.callback_url or '').strip() if user else ''
        if not callback_token and user:
            callback_token = (getattr(user, 'callback_token', None) or '').strip()

    if user and int(getattr(user, 'callback_enabled', 1) or 1) != 1 and not (data.get('force') is True):
        return ServerError(msg='Callback is disabled')

    if not callback_url:
        return ServerError(msg='Callback url is required')

    if not callback_url.lower().startswith(('http://', 'https://')):
        return ServerError(msg='Callback url must start with http:// or https://')

    if not bus_id:
        bus_id = 'test_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')

    if detect_data is None:
        detect_data = {
            'topic': 'test_callback',
            'result': {'label': 'test', 'confidence': 99.9}
        }

    payload = {
        'bus_id': bus_id,
        'time': datetime.datetime.now().strftime(get_second_format()),
        'detect_data': detect_data
    }

    try:
        headers = {}
        if callback_token:
            headers['Authorization'] = f'Bearer {callback_token}'
            headers['X-Callback-Token'] = callback_token
        resp = requests.post(callback_url, json=payload, headers=headers, timeout=8)
        return Success(data={
            'request': payload,
            'status_code': resp.status_code,
            'response_text': (resp.text or '')[:2000]
        })
    except Exception as e:
        return ServerError(msg=f'Callback test failed: {str(e)}')


@api.route('/refresh', methods=['POST'])
def refresh_token():
    """刷新Token接口
    
    流程：
    1. 接收Refresh Token
    2. 验证Refresh Token
    3. 生成新的Access Token
    4. 返回新的Access Token
    """
    data = request.json
    if not data or 'refresh_token' not in data:
        return ServerError(msg='Refresh token is required')

    refresh_token = data['refresh_token']

    try:
        # 11. 验证Refresh Token
        user_info = verify_refresh_token(refresh_token)

        # 12. 生成新的Access Token
        new_access_token = generate_access_token(user_info['uid'], 'user')

        # 13. 返回新的Access Token
        return Success(data={
            'access_token': new_access_token,
            'token_type': 'Bearer',
            'expires_in': 15 * 60  # 15分钟，单位秒
        })
    except TokenFailed as e:
        return AuthFailed(msg='Invalid refresh token')
    except Exception as e:
        return AuthFailed(msg='Token refresh failed')


@api.route('/logout', methods=['POST'])
@login_required
def logout():
    return Success(msg='Logout successful')


@api.route('/ttttt', methods=['POST'])
@login_required
def ttttt():
    return Success()
