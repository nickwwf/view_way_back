# coding: utf-8
from datetime import datetime
from app.libs.error_code import NotFound, ServerError
from app.models.s_recognition_result import SRecognitionResult
from app.models.base import db
from app.models.s_recognition_node import SRecognitionNode
from app.models.s_user import SUser
from app.models.s_ai_asset_config import SAIAssetConfig
from app.mq.pub.publish_message import SendMQ
from app.repos.consumption_repo import ConsumptionRepo


class RecognitionResultRepo:
    @staticmethod
    def _normalize_detect_alg_ids(detect_alg):
        if detect_alg is None:
            return []
        if isinstance(detect_alg, (list, tuple)):
            items = detect_alg
        else:
            items = [detect_alg]

        ids = []
        for item in items:
            if not item:
                continue
            if isinstance(item, str):
                v = item.strip()
                if v:
                    ids.append(v)
                continue
            if isinstance(item, dict):
                v = item.get('id') or item.get('alg_id') or item.get('ai_asset_id')
                if v:
                    ids.append(str(v).strip())
                continue
        return [x for x in ids if x]

    @staticmethod
    def _validate_detect_alg(user_id, detect_alg, session=None):
        sess = session or db.session
        alg_ids = RecognitionResultRepo._normalize_detect_alg_ids(detect_alg)
        if not alg_ids:
            raise ServerError(msg='detect_alg is required')

        user = sess.query(SUser).filter_by(id=user_id).first()
        user_ai_assets = (user.ai_asset or []) if user else []
        user_ai_assets = [str(x) for x in user_ai_assets if x]
        allowed_set = set(user_ai_assets)

        if allowed_set and any(aid not in allowed_set for aid in alg_ids):
            raise ServerError(msg='Invalid detect_alg: contains unauthorized algorithm')

        valid_count = sess.query(SAIAssetConfig).filter(
            SAIAssetConfig.id.in_(alg_ids),
            SAIAssetConfig.status == 1,
            SAIAssetConfig.is_del == 0
        ).count()
        if valid_count != len(set(alg_ids)):
            raise ServerError(msg='Invalid detect_alg: contains disabled or deleted algorithm')

    @staticmethod
    def create_recognition_results_batch(user_id, image_data_list, algorithm_type, detect_alg):
        """
        批量创建识别结果
        :param user_id: 用户ID
        :param image_data_list: 图片数据列表，可以是 URL 列表或字典列表 [{'image_url': '...', 'thumbnail_url': '...'}]
        :param algorithm_type: 算法类型
        :param detect_alg: 检测算法
        :return: 识别结果列表
        """
        RecognitionResultRepo._validate_detect_alg(user_id, detect_alg)
        date_str = datetime.now().strftime('%Y%m%d%H%M%S')
        recognitions = []

        for idx, image_data in enumerate(image_data_list):
            recognition = SRecognitionResult()
            recognition.image_no = f"IMG{date_str}{str(idx+1).zfill(3)}"
            
            if isinstance(image_data, dict):
                recognition.image_url = image_data.get('image_url')
                recognition.thumbnail_url = image_data.get('thumbnail_url')
            else:
                recognition.image_url = image_data
                recognition.thumbnail_url = None
                
            recognition.user_id = user_id
            recognition.algorithm_type = algorithm_type
            recognition.status = 'waiting'
            recognition.recognition_result = {}
            recognition.detect_alg = detect_alg
            recognitions.append(recognition)

        msgs = []
        with db.auto_commit():
            db.session.add_all(recognitions)
            db.session.flush()

            amount = ConsumptionRepo.calc_amount(detect_alg, session=db.session)
            for recognition in recognitions:
                node = SRecognitionNode()
                node.recognition_id = recognition.id
                node.node_type = "waiting"
                node.node_info = {}
                db.session.add(node)

                ConsumptionRepo.create_pre_consumption(
                    user_id=user_id,
                    recognition_id=recognition.id,
                    amount=amount,
                    description=f"识别预扣费: {recognition.image_no}",
                    session=db.session,
                    auto_commit=False
                )
                msgs.append({"image_url": recognition.image_url, "bus_id": recognition.id, "detect_alg": recognition.detect_alg})

            for msg in msgs:
                SendMQ.publish_begin_detect(msg)
        return recognitions

    @staticmethod
    def get_recognition_result_by_id(recognition_id):
        return SRecognitionResult.query.filter_by(id=recognition_id).first()

    @staticmethod
    def get_recognition_results_by_user_id(user_id, page=1, page_size=20, search=None, status_list=None):
        filters = [SRecognitionResult.user_id == user_id]
        if search:
            filters.append(SRecognitionResult.image_no.like(f"%{search}%"))
        if status_list:
            filters.append(SRecognitionResult.status.in_(status_list))

        query = db.session.query(SRecognitionResult).filter(*filters).order_by(SRecognitionResult.create_time.desc())
        pagination = query.paginate(page=page, per_page=page_size, error_out=False)
        return pagination

    @staticmethod
    def get_all_recognition_results(page=1, page_size=20, search=None, status_list=None):
        filters = []
        if search:
            filters.append(SRecognitionResult.image_no.like(f"%{search}%"))
        if status_list:
            filters.append(SRecognitionResult.status.in_(status_list))

        query = db.session.query(SRecognitionResult).filter(*filters).order_by(SRecognitionResult.create_time.desc())
        pagination = query.paginate(page=page, per_page=page_size, error_out=False)
        return pagination

    @staticmethod
    def update_recognition_result(recognition_id, params):
        recognition = RecognitionResultRepo.get_recognition_result_by_id(recognition_id)
        if not recognition:
            raise NotFound(msg='Recognition result not found')

        for key, value in params.items():
            if hasattr(recognition, key):
                setattr(recognition, key, value)

        with db.auto_commit():
            pass
        return recognition
