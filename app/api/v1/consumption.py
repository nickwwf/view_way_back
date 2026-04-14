# coding: utf-8
from flask import request, g

from app.libs.define_print import DefinePrint
from app.repos.consumption_repo import ConsumptionRepo
from app.repos.user_repo import UserRepo
from app.libs.token_auth import login_required
from app.libs.error_code import Success, ServerError, NotFound

api = DefinePrint('consumption')


@api.route('/balance', methods=['GET'])
@login_required
def get_user_balance():
    # 从g中获取用户信息
    user_id = getattr(g, 'user_id', None)
    if not user_id:
        # 如果g中没有用户信息，通过app_key查询
        app_key = request.args.get('app_key')
        if not app_key:
            return ServerError(msg='App key is required')
        user = UserRepo.get_user_by_app_key(app_key)
        if not user:
            return NotFound(msg='User not found')
        user_id = user.id
    
    balance = ConsumptionRepo.get_user_balance(user_id)
    
    return Success(data={
        'balance': balance
    })


@api.route('/list', methods=['GET'])
@login_required
def get_consumption_list():
    # 从g中获取用户信息
    user_id = getattr(g, 'user_id', None)
    if not user_id:
        # 如果g中没有用户信息，通过app_key查询
        app_key = request.args.get('app_key')
        if not app_key:
            return ServerError(msg='App key is required')
        user = UserRepo.get_user_by_app_key(app_key)
        if not user:
            return NotFound(msg='User not found')
        user_id = user.id
    
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    
    # 获取筛选参数
    filters = {}
    if 'consumption_type' in request.args:
        filters['consumption_type'] = request.args.get('consumption_type')
    if 'status' in request.args:
        filters['status'] = request.args.get('status')
    if 'start_time' in request.args:
        filters['start_time'] = request.args.get('start_time')
    if 'end_time' in request.args:
        filters['end_time'] = request.args.get('end_time')
    
    consumption_list, total = ConsumptionRepo.get_consumption_list(user_id, page, size, filters)
    
    return Success(data={
        'list': consumption_list,
        'total': total,
        'page': page,
        'size': size
    })


@api.route('/deduct_list', methods=['GET'])
@login_required
def get_deduct_consumption_list():
    user_id = getattr(g, 'user_id', None)
    if not user_id:
        app_key = request.args.get('app_key')
        if not app_key:
            return ServerError(msg='App key is required')
        user = UserRepo.get_user_by_app_key(app_key)
        if not user:
            return NotFound(msg='User not found')
        user_id = user.id

    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)

    filters = {
        'consumption_type': request.args.get('consumption_type') if 'consumption_type' in request.args else None,
        'status': request.args.get('status') if 'status' in request.args else None,
        'start_time': request.args.get('start_time') if 'start_time' in request.args else None,
        'end_time': request.args.get('end_time') if 'end_time' in request.args else None,
        'search': request.args.get('search') if 'search' in request.args else None,
    }

    items, total, summary = ConsumptionRepo.get_deduct_consumption_list(user_id, page, size, filters)

    return Success(data={
        'list': items,
        'total': total,
        'page': page,
        'size': size,
        'summary': summary
    })


@api.route('/recharge', methods=['POST'])
@login_required
def recharge_balance():
    data = request.json
    if not data or 'amount' not in data:
        return ServerError(msg='Amount is required')
    
    # 从g中获取用户信息
    user_id = getattr(g, 'user_id', None)
    if not user_id:
        # 如果g中没有用户信息，通过app_key查询
        app_key = data.get('app_key')
        if not app_key:
            return ServerError(msg='App key is required')
        user = UserRepo.get_user_by_app_key(app_key)
        if not user:
            return NotFound(msg='User not found')
        user_id = user.id
    
    user = ConsumptionRepo.update_user_balance(user_id, data['amount'])
    if not user:
        return NotFound(msg='User not found')
    
    return Success(data={
        'balance': user.balance
    }, msg='Recharge successful')
