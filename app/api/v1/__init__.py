from flask import Blueprint
from app.api.v1 import user, data, consumption, ai_asset_config, recognition_result, detect_api, task_image


def create_blueprint_v1():
    bp_v1 = Blueprint('v1', __name__)
    user.api.register(bp_v1)
    data.api.register(bp_v1)
    consumption.api.register(bp_v1)
    ai_asset_config.api.register(bp_v1)
    recognition_result.api.register(bp_v1)
    detect_api.api.register(bp_v1)
    task_image.api.register(bp_v1)
    return bp_v1
