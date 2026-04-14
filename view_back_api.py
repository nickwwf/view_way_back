
import traceback

from flask import request

from app import init_app
from app.env import base_path
from app.libs.error_code import ServerError
from app.libs.logger import logger
from app.libs.response import APIResponse

app = init_app()

@app.errorhandler(Exception)
def framework_error(e):
    error_msg = traceback.format_exc()
    logger.error(f"error_msg: {error_msg}")
    if isinstance(e, APIResponse):
        return e
    else:
        if not app.config['DEBUG']:
            return ServerError()
        else:
            raise e

@app.before_request
def before_request():
    # TODO 保存日志
    pass

# TODO after_request 保存日志

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='6001', debug=True)
    #app.run(host='0.0.0.0', port='6001', debug='DEBUG')
