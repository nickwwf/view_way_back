from .app import Flask
from .app import rabbit
from .env import load_env
from .mq.subs.sub_detect_process import SubDetectProcess, MonitorDetectProcess

from app.plug.rabbit import RabbitMq
from flask_cors import CORS


def register_blueprints(app):
    from app.api.v1 import create_blueprint_v1
    app.register_blueprint(create_blueprint_v1(), url_prefix='/v1')


def register_plugin(app):
    from app.models.base import db
    db.init_app(app)
    from init_db import init_database
    init_database(app)


def init_app():
    app = Flask(__name__)
    env = load_env()  # 可以自定义路径
    print(f"\033[1;32m注意:当前项目运行的环境为{env['FLASK_CONFIG']}\033[0m")
    flask_env = env['FLASK_CONFIG'] or 'dev'
    app.config.from_object(f'app.config.{flask_env}')
    # 跨域
    CORS(app, supports_credentials=True)
    register_plugin(app)
    rabbit.init_app(app)
    register_blueprints(app)

    detect = MonitorDetectProcess(daemon=True)  # 监听航线架次  # 保留
    detect.start()

    return app
