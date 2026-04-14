# coding: utf-8
from datetime import datetime

from app.models.s_data import SData
from app.models.base import db

class DataRepo:
    @staticmethod
    def create_data(data):
        data_obj = SData()
        data_obj.name = data.get('name')
        data_obj.type = data.get('type')
        data_obj.status = data.get('status', 'active')
        data_obj.description = data.get('description')
        data_obj.created_at = datetime.now()
        
        with db.auto_commit():
            db.session.add(data_obj)
        
        return data_obj
    
    @staticmethod
    def get_data_by_id(data_id):
        return SData.query.filter_by(id=data_id).first()
    
    @staticmethod
    def get_data_list(page=1, size=10):
        pagination = SData.query.paginate(
            page=page,
            per_page=size,
            error_out=False
        )
        
        data_list = []
        for data in pagination.items:
            data_list.append({
                'id': data.id,
                'name': data.name,
                'type': data.type,
                'status': data.status,
                'description': data.description,
                'created_at': data.created_at.strftime('%Y-%m-%d %H:%M:%S') if data.created_at else None
            })
        
        return data_list, pagination.total
    
    @staticmethod
    def update_data(data_id, data):
        data_obj = SData.query.filter_by(id=data_id).first()
        if not data_obj:
            return None
        
        if 'name' in data:
            data_obj.name = data['name']
        if 'type' in data:
            data_obj.type = data['type']
        if 'status' in data:
            data_obj.status = data['status']
        if 'description' in data:
            data_obj.description = data['description']
        
        with db.auto_commit():
            db.session.add(data_obj)
        
        return data_obj
    
    @staticmethod
    def delete_data(data_id):
        data_obj = SData.query.filter_by(id=data_id).first()
        if not data_obj:
            return False
        
        with db.auto_commit():
            db.session.delete(data_obj)
        
        return True
