# coding: utf-8
from app.repos.user_repo import UserRepo
from app.models.base import db


def init_database(app):
    with app.app_context():
        print('开始初始化数据库...')

        db.create_all()

        existing_user = UserRepo.get_user_by_app_key('f70fc0d4a3f8421ab1492fa6b88f1222')
        if not existing_user:
            print('创建默认用户...')

            from app.models import SUser
            user = SUser()
            user.id = 'view_way_admin_2026'
            user.app_key = 'f70fc0d4a3f8421ab1492fa6b88f1222'
            user.app_secret = 'JMiBYgFuB7v9Ppwyx9QxoY4sZIckBMPK'
            user.user_name = '管理员'

            with db.auto_commit():
                db.session.add(user)

            print(f'默认用户创建成功: App Key = {user.app_key}')
        else:
            print('默认用户已存在')

        print('数据库初始化完成！')
