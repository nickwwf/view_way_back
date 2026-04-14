# coding: utf-8
import secrets
import string
import uuid
from datetime import datetime

from app.libs.error_code import NotFound, ServerError
from app.models.s_user import SUser
from app.models.base import db


class UserRepo:
    @staticmethod
    def create_user(params):
        """
        创建普通用户
        """
        app_secret = UserRepo._generate_app_secret()

        user = SUser()
        user.id = uuid.uuid4().hex
        user.user_name = params['user_name']
        user.status = params['status']
        user.balance = params['balance']
        user.ai_asset = params['ai_asset']
        user.app_key = uuid.uuid4().hex
        user.app_secret = app_secret

        with db.auto_commit():
            db.session.add(user)
            db.session.flush()
        return user

    @staticmethod
    def get_user_by_app_key(app_key):
        return SUser.query.filter_by(app_key=app_key).first()

    @staticmethod
    def get_user_by_id(user_id):
        return SUser.query.filter_by(id=user_id).first()

    @staticmethod
    def get_user_list(page=1, size=10):
        pagination = SUser.query.paginate(
            page=page,
            per_page=size,
            error_out=False
        )

        users = []
        for user in pagination.items:
            users.append({
                'id': user.id,
                'app_key': user.app_key,
                'app_secret': user.app_secret,
                'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else None
            })

        return users, pagination.total

    @staticmethod
    def update_user(user_id, params):
        user = SUser.query.filter_by(id=user_id).first()
        if not user:
            raise NotFound(msg="不存在此用户")
        with db.auto_commit():
            user.user_name = params['user_name']
            user.status = params['status']
            user.balance = params['balance']
            user.ai_asset = params['ai_asset']

        return user

    @staticmethod
    def delete_user(user_id):
        user = SUser.query.filter_by(id=user_id).first()
        if not user:
            raise NotFound(msg="不存在此用户")
        if user.id == "view_way_admin_2026":
            raise ServerError(msg="无法删除此账户", code=200)

        with db.auto_commit():
            db.session.delete(user)

    @staticmethod
    def _generate_app_secret(length=32):
        alphabet = string.ascii_letters + string.digits
        app_secret = ''.join(secrets.choice(alphabet) for _ in range(length))
        return app_secret
