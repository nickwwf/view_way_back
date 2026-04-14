# coding: utf-8
from flask import request, g

from app.libs.define_print import DefinePrint
from app.repos.data_repo import DataRepo
from app.libs.token_auth import login_required
from app.libs.error_code import Success, ServerError, NotFound

api = DefinePrint('data')


@api.route('/list', methods=['GET'])
@login_required
def get_data_list():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    
    data_list, total = DataRepo.get_data_list(page, size)
    
    return Success(data={
        'list': data_list,
        'total': total,
        'page': page,
        'size': size
    })


@api.route('/<int:data_id>', methods=['GET'])
@login_required
def get_data_detail(data_id):
    data = DataRepo.get_data_by_id(data_id)
    if not data:
        return NotFound(msg='Data not found')
    
    return Success(data={
        'id': data.id,
        'name': data.name,
        'type': data.type,
        'status': data.status,
        'description': data.description,
        'created_at': data.created_at.strftime('%Y-%m-%d %H:%M:%S') if data.created_at else None
    })


@api.route('', methods=['POST'])
@login_required
def create_data():
    data = request.json
    if not data or 'name' not in data:
        return ServerError(msg='Name is required')
    
    data_obj = DataRepo.create_data(data)
    
    return Success(data={
        'id': data_obj.id,
        'name': data_obj.name,
        'type': data_obj.type,
        'status': data_obj.status,
        'description': data_obj.description
    }, msg='Create successful')


@api.route('/<int:data_id>', methods=['PUT'])
@login_required
def update_data(data_id):
    data = request.json
    if not data:
        return ServerError(msg='Invalid data')
    
    data_obj = DataRepo.get_data_by_id(data_id)
    if not data_obj:
        return NotFound(msg='Data not found')
    
    data_obj = DataRepo.update_data(data_id, data)
    
    return Success(data={
        'id': data_obj.id,
        'name': data_obj.name,
        'type': data_obj.type,
        'status': data_obj.status,
        'description': data_obj.description
    }, msg='Update successful')


@api.route('/<int:data_id>', methods=['DELETE'])
@login_required
def delete_data(data_id):
    data_obj = DataRepo.get_data_by_id(data_id)
    if not data_obj:
        return NotFound(msg='Data not found')
    
    DataRepo.delete_data(data_id)
    
    return Success(msg='Delete successful')
