# coding: utf-8
"""
提供给第三方接入的接口
"""
import time
import requests
from flask import g, request
from sqlalchemy import and_, func

from app.libs.define_print import DefinePrint
from app.libs.file_helper import FileHelper
from app.libs.token_auth import login_required
from app.libs.error_code import Success, ServerError, TooManyRequests
from app.libs.redis_util import Redis
from app.models import SUser
from app.models.base import db
from app.models.s_ai_asset_config import SAIAssetConfig
from app.models.s_recognition_node import SRecognitionNode
from app.models.s_recognition_result import SRecognitionResult
from app.repos.recognition_result_repo import RecognitionResultRepo

api = DefinePrint('detect')


@api.route('/img', methods=['POST'])
@login_required
def create_img_detect():
    """
    外部系统接入：创建识别结果
    入参：image_url, detect_alg, algorithm_type
    """
    data = request.json
    if not data or 'image_url' not in data or 'detect_alg' not in data:
        return ServerError(msg='image_url and detect_alg are required')

    image_url = data['image_url']
    detect_alg = data['detect_alg']
    algorithm_type = data.get('algorithm_type', '')
    user_id = g.user_id

    # 1. 获取图片内容
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        image_data = response.content
        content_type = response.headers.get('Content-Type')
        
        # 尝试从 URL 或 Content-Type 获取后缀
        file_ext = 'jpg'
        if '.' in image_url:
            file_ext = image_url.rsplit('.', 1)[-1].lower()
            if len(file_ext) > 4: file_ext = 'jpg' # 防止带参数的 URL
        elif content_type and '/' in content_type:
            file_ext = content_type.split('/')[-1]
            
    except Exception as e:
        return ServerError(msg=f'Failed to fetch image from URL: {str(e)}')

    # 2. 生成缩略图并上传到 MinIO
    try:
        # 只上传缩略图，原图使用外部提供的 URL
        upload_result = FileHelper.upload_bytes(
            data=image_data,
            file_ext=file_ext,
            sub_folder='external_thumbs',
            make_thumbnail=True,
            content_type=content_type
        )
        thumbnail_url = upload_result.get('thumbnail_url')
    except Exception as e:
        return ServerError(msg=f'Failed to process thumbnail: {str(e)}')

    # 3. 创建识别结果记录
    params = {
        'image_no': f"EXT{user_id[:4]}", # 临时编号，Repo 会根据逻辑重新生成
        'image_url': image_url,
        'thumbnail_url': thumbnail_url,
        'user_id': user_id,
        'algorithm_type': algorithm_type,
        'detect_alg': detect_alg
    }
    
    # 注意：RecognitionResultRepo.create_recognition_result 需要 image_no，
    # 但我们批量创建方法会自动生成编号。这里我们统一使用 Repo 的逻辑。
    # 为了方便，我们直接调用 create_recognition_results_batch 传入单张图片
    
    recognitions = RecognitionResultRepo.create_recognition_results_batch(
        user_id=user_id,
        image_data_list=[{
            'image_url': image_url,
            'thumbnail_url': thumbnail_url
        }],
        algorithm_type=algorithm_type,
        detect_alg=detect_alg
    )

    if not recognitions:
        return ServerError(msg='Failed to create recognition result record')

    r = recognitions[0]
    return Success(data={
        'id': r.id,
        'image_no': r.image_no,
        'image_url': r.image_url,
        'thumbnail_url': r.thumbnail_url,
        'algorithm_type': r.algorithm_type
    }, msg='External recognition result created successfully')

@api.route('/result/pull', methods=['GET'])
@login_required
def pull_img_detect_result():
    user_id = g.user_id
    try:
        rds = Redis._get_r()
        key = f"rl:detect:result_pull:{user_id}"
        ok = rds.set(key, str(int(time.time())), ex=1, nx=True)
        if not ok:
            return TooManyRequests(msg='请求过于频繁，请稍后再试')
    except Exception:
        pass

    limit = request.args.get('limit', 20, type=int)
    if not limit or limit < 1:
        limit = 20
    if limit > 100:
        limit = 100

    items = []
    with db.auto_commit():
        recs = (db.session.query(SRecognitionResult)
                .filter(
                    SRecognitionResult.user_id == user_id,
                    SRecognitionResult.status.in_(['success', 'fail'])
                )
                .order_by(SRecognitionResult.create_time.asc())
                .with_for_update()
                .limit(limit)
                .all())

        if not recs:
            return Success(data={'total': 0, 'list': []})

        rec_ids = [r.id for r in recs]

        latest_node_time_sq = db.session.query(
            SRecognitionNode.recognition_id.label('rid'),
            func.max(SRecognitionNode.create_time).label('max_ct')
        ).filter(
            SRecognitionNode.recognition_id.in_(rec_ids)
        ).group_by(
            SRecognitionNode.recognition_id
        ).subquery()

        latest_nodes = db.session.query(
            SRecognitionNode.recognition_id,
            SRecognitionNode.node_type,
            SRecognitionNode.node_info,
            SRecognitionNode.create_time
        ).join(
            latest_node_time_sq,
            and_(
                SRecognitionNode.recognition_id == latest_node_time_sq.c.rid,
                SRecognitionNode.create_time == latest_node_time_sq.c.max_ct
            )
        ).all()

        node_map = {}
        for rid, node_type, node_info, node_ct in latest_nodes:
            if rid not in node_map:
                node_map[rid] = {
                    'node_type': node_type,
                    'node_info': node_info,
                    'create_time': node_ct
                }

        for r in recs:
            node = node_map.get(r.id) or {}
            detect_data = node.get('node_info') or {}
            status = node.get('node_type') or (r.status or '')

            items.append({
                'id': r.id,
                'image_no': r.image_no,
                'image_url': r.image_url,
                'thumbnail_url': r.thumbnail_url,
                'algorithm_type': r.algorithm_type,
                'status': status,
                'detect_data': detect_data,
                'create_time': r.create_time.strftime('%Y-%m-%d %H:%M:%S') if r.create_time else None
            })

            r.status = 'output'
            db.session.add(r)

            out_node = SRecognitionNode()
            out_node.recognition_id = r.id
            out_node.node_type = 'output'
            out_node.node_info = detect_data
            db.session.add(out_node)

        db.session.flush()

    return Success(data={'total': len(items), 'list': items})

@api.route('/all_rules', methods=['GET'])
@login_required
def get_all_rules():
    """
    获取当前用户权限下所有有效的算法
    """
    user_id = g.user_id
    user = SUser.query.filter_by(id=user_id).first()
    if not user:
        return ServerError(msg='User not found')

    ai_asset_ids = user.ai_asset or []
    if not ai_asset_ids:
        return Success(data=[])

    configs = SAIAssetConfig.query.filter(
        SAIAssetConfig.status == 1,
        SAIAssetConfig.is_del == 0,
        SAIAssetConfig.id.in_(ai_asset_ids)
    ).all()

    items = []
    for config in configs:
        items.append({
            'id': config.id,
            'ai_name': config.ai_name,
            'price': config.price,
            'description': config.description
        })
    return Success(data=items)
