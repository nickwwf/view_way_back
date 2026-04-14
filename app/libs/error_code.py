# coding: utf-8
from app.libs.response import APIResponse


class Success(APIResponse):
    code = 200
    msg = '成功'
    error_code = 0


class AuthFailed(APIResponse):
    code = 401
    msg = '认证失败'
    error_code = 1001


class TokenFailed(APIResponse):
    code = 401
    msg = '访问token无效'
    error_code = 1002


class TokenExpired(APIResponse):
    code = 401
    msg = '访问token无效'
    error_code = 1003


class Forbidden(APIResponse):
    code = 403
    msg = '禁止访问'
    error_code = 1004


class NotFound(APIResponse):
    code = 404
    msg = '不存在该数据'
    error_code = 1005


class ServerError(APIResponse):
    code = 500
    msg = '服务错误'
    error_code = 999

    
class ParameterException(APIResponse):
    code = 400
    msg = '参数无效'
    error_code = 1000


class TooManyRequests(APIResponse):
    code = 429
    msg = '请求过于频繁'
    error_code = 1006
