import datetime
from collections import namedtuple

from flask import current_app, g, request
import jwt
from jwt import PyJWTError

from app.env import load_conf
from app.libs.error_code import AuthFailed, TokenFailed, TokenExpired, Forbidden
from app.libs.scope import is_in_scope
from app.models import SUser
from app.models.base import db

# Token配置
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Access Token 15分钟过期
REFRESH_TOKEN_EXPIRE_DAYS = 7     # Refresh Token 7天过期


def generate_access_token(uid, ac_type, scope=None):
    """生成Access Token，有效期15分钟"""
    secret_key = load_conf.get('SECRET_KEY')
    payload = {
        'uid': uid,
        'type': ac_type,
        'scope': scope,
        'token_type': 'access',
        'exp': datetime.datetime.now() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    return jwt.encode(payload, secret_key, algorithm='HS256')


def generate_refresh_token(uid, ac_type, scope=None):
    """生成Refresh Token，有效期7天"""
    secret_key = load_conf.get('SECRET_KEY')
    payload = {
        'uid': uid,
        'type': ac_type,
        'scope': scope,
        'token_type': 'refresh',
        'exp': datetime.datetime.now() + datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    }
    return jwt.encode(payload, secret_key, algorithm='HS256')


def generate_token_pair(uid, ac_type, scope=None):
    """生成Access Token和Refresh Token对"""
    access_token = generate_access_token(uid, ac_type, scope)
    refresh_token = generate_refresh_token(uid, ac_type, scope)
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': ACCESS_TOKEN_EXPIRE_MINUTES * 60  # 秒
    }


def generate_token(uid, ac_type, scope=None):
    """向后兼容：生成单个Token（用于旧代码）"""
    return generate_access_token(uid, ac_type, scope)


# 验证 token 合法性
def verify_auth_token(token, token_type='access'):
    """验证Token合法性
    
    Args:
        token: JWT Token
        token_type: 'access' 或 'refresh'
    
    Returns:
        解码后的Token数据
    """
    secret_key = current_app.config['SECRET_KEY']
    try:
        data = jwt.decode(token, secret_key, algorithms=['HS256'])
        # 验证Token类型
        if data.get('token_type') != token_type:
            raise TokenFailed(msg=f'Invalid token type, expected {token_type}')
        return data
    except jwt.ExpiredSignatureError:
        raise TokenExpired()    # token 过期
    except PyJWTError:
        raise TokenFailed()  # token 无效


# 解析 token 获取当前登录用户的相关信息
def get_user_by_token(token):
    # 先验证 token 合法性
    data = verify_auth_token(token, token_type='access')
    uid = data['uid']
    ac_type = data['type']
    scope = data['scope']

    _user = db.session.query(SUser).filter(SUser.id == uid).first()
    if not _user:
        raise Forbidden()  # 无权访问

    # 验证当前用户是否有足够的权限访问当前视图
    allow = is_in_scope(scope, request.endpoint)
    if not allow:
        raise Forbidden()  # 无权访问

    g.user_id = _user.id
    g.user_name = _user.user_name

    return

def verify_refresh_token(token):
    """验证Refresh Token并返回用户信息"""
    data = verify_auth_token(token, token_type='refresh')
    return data


# 自定义装饰器，用于JWT认证
def login_required(f):
    """JWT认证装饰器
    
    支持两种认证方式：
    1. Authorization: Bearer <token>（推荐）
    2. Authorization: Basic base64(token:)（向后兼容）
    """
    def decorated_function(*args, **kwargs):
        token = None
        
        # 从请求头获取Authorization
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            # 检查是否是Bearer Token
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
            # 检查是否是Basic Auth（向后兼容）
            elif auth_header.startswith('Basic '):
                import base64
                try:
                    encoded_part = auth_header.split(' ')[1]
                    decoded = base64.b64decode(encoded_part).decode('utf-8')
                    token = decoded.split(':')[0]
                except:
                    pass
        
        if not token:
            raise AuthFailed(msg='Authorization header is required')
        
        # 验证Token
        try:
            get_user_by_token(token)
        except Exception as e:
            raise AuthFailed(msg='Invalid or expired token')

        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function