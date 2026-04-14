from flask import request, json
from werkzeug.exceptions import HTTPException

from app.libs.utils import NpEncoder


class APIResponse(HTTPException):
    code = 500  # 默认错误码 500, 表示未知错误
    msg = 'sorry, we make a mistake (*-_-)!'
    error_code = 999
    data = None     # 用于存放返回结果

    def __init__(self, msg=None, code=None, error_code=None, data=None, headers=None):
        if code:
            self.code = code
        if error_code:
            self.error_code = error_code
        if msg:
            self.msg = msg
        if data:
            self.data = data
        super(APIResponse, self).__init__(msg, None)

    def get_body(self, environ=None, scope=None, ) -> str:
        body = dict(
            msg=self.msg,
            error_code=self.error_code,
            request=request.method + ' ' + self.get_url_no_param(),
            data=self.data
        )
        text = json.dumps(body, cls=NpEncoder)
        return text

    def get_headers(self, environ=None, scope=None, ):
        return [('Content-Type', 'application/json')]

    @staticmethod
    def get_url_no_param():
        full_path = str(request.full_path)
        main_path = full_path.split('?')
        return main_path[0]
