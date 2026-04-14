# coding: utf-8
from flask import request, g

from app.libs.define_print import DefinePrint
from app.libs.helper import iPagenation
from app.libs.token_auth import login_required
from app.libs.error_code import Success, ServerError
from app.models import SRecognitionNode, SRecognitionResult
from app.models.base import db
from app.models.s_consumption import SConsumption
from app.models.s_ai_asset_config import SAIAssetConfig
from app.repos.recognition_result_repo import RecognitionResultRepo
from app.validators.recognition_result_forms import CreateRecognitionResultForm, UpdateRecognitionResultForm, RecognitionResultListForm
from sqlalchemy import func, and_
from datetime import datetime, timedelta

api = DefinePrint('recognition_result')


@api.route('/create', methods=['POST'])
@login_required
def create_recognition_result():
    form = CreateRecognitionResultForm().validate_for_api()
    user_id = g.user_id
    image_urls = form.image_urls.data
    algorithm_type = form.algorithm_type.data
    detect_alg = form.detect_alg.data

    recognitions = RecognitionResultRepo.create_recognition_results_batch(
        user_id=user_id,
        image_data_list=image_urls,
        algorithm_type=algorithm_type,
        detect_alg=detect_alg
    )

    items = []
    for r in recognitions:
        items.append({
            'id': r.id,
            'image_no': r.image_no,
            'image_url': r.image_url,
            'thumbnail_url': r.thumbnail_url,
            'algorithm_type': r.algorithm_type
        })

    return Success(data={
        'total': len(recognitions),
        'list': items
    }, msg='Recognition results created successfully')


@api.route('/detail/<string:recognition_id>', methods=['GET'])
@login_required
def get_recognition_result(recognition_id):
    recognition = RecognitionResultRepo.get_recognition_result_by_id(recognition_id)
    if not recognition:
        return ServerError(msg='Recognition result not found')
    detect_alg_raw = recognition.detect_alg
    if isinstance(detect_alg_raw, str):
        detect_alg_raw = [detect_alg_raw]
    if not isinstance(detect_alg_raw, list):
        detect_alg_raw = []

    alg_ids = []
    for item in detect_alg_raw:
        if isinstance(item, str):
            alg_ids.append(item)
        elif isinstance(item, dict):
            aid = item.get('id') or item.get('alg_id') or item.get('ai_asset_id')
            if aid:
                alg_ids.append(aid)

    alg_configs = db.session.query(SAIAssetConfig).filter(
        SAIAssetConfig.id.in_(alg_ids)
    ).all() if alg_ids else []
    
    alg_map = {c.id: {'id': c.id, 'name': c.ai_name, 'price': c.price} for c in alg_configs}
    
    detect_algs = []
    for item in detect_alg_raw:
        if isinstance(item, str):
            if item in alg_map:
                detect_algs.append(alg_map[item])
            else:
                detect_algs.append({'id': item, 'name': item, 'price': 0})
        elif isinstance(item, dict):
            aid = item.get('id') or item.get('alg_id') or item.get('ai_asset_id')
            if aid and aid in alg_map:
                # Merge the DB info into the dict
                new_item = dict(item)
                new_item['name'] = alg_map[aid]['name']
                if 'price' not in new_item:
                    new_item['price'] = alg_map[aid]['price']
                detect_algs.append(new_item)
            else:
                detect_algs.append(item)

    _rec = {
        'id': recognition.id,
        'image_no': recognition.image_no,
        'image_url': recognition.image_url,
        'thumbnail_url': recognition.thumbnail_url,
        'algorithm_type': recognition.algorithm_type,
        'recognition_result': recognition.recognition_result,
        'detect_alg': detect_algs,
        'create_time': recognition.create_time.strftime('%Y-%m-%d %H:%M:%S') if recognition.create_time else None
    }
    nodes = db.session.query(SRecognitionNode).filter_by(recognition_id=recognition_id).order_by(SRecognitionNode.create_time.asc()).all()
    _nodes = []
    for node in nodes:
        _nodes.append({
            'id': node.id,
            'recognition_id': node.recognition_id,
            'node_type': node.node_type,
            'node_info': node.node_info,
            'create_time': node.create_time.strftime('%Y-%m-%d %H:%M:%S') if node.create_time else None
        })
    _rec['nodes'] = _nodes
    _rec['status'] = _nodes[-1]['node_type'] if _nodes else ''

    consumptions = db.session.query(SConsumption).filter_by(recognition_id=recognition_id).order_by(SConsumption.create_time.asc()).all()
    records = []
    sums = {'pre': 0.0, 'down': 0.0, 'back': 0.0, 'total': 0.0}
    for c in consumptions:
        try:
            amt = float(c.amount or 0)
        except Exception:
            amt = 0.0
        status = c.status or ''
        if status in sums:
            sums[status] += amt
        sums['total'] += amt
        records.append({
            'id': c.id,
            'amount': amt,
            'status': status,
            'consumption_type': c.consumption_type,
            'description': c.description,
            'create_time': c.create_time.strftime('%Y-%m-%d %H:%M:%S') if c.create_time else None
        })
    _rec['consumption'] = {
        'pre': float(sums['pre']),
        'down': float(sums['down']),
        'back': float(sums['back']),
        'total': float(sums['total']),
        'records': records
    }
    return Success(data=_rec)


@api.route('/list', methods=['GET'])
@login_required
def get_recognition_results():
    form = RecognitionResultListForm().validate_for_api()
    user_id = g.user_id
    is_admin = (user_id == "view_way_admin_2026")

    page = form.page.data
    page_size = form.page_size.data
    search = form.search.data if form.search.data else None
    status_list = None
    if getattr(form, 'status', None) and form.status.data:
        raw = str(form.status.data)
        status_list = [s.strip() for s in raw.split(',') if s.strip()]

    if is_admin:
        pagination = RecognitionResultRepo.get_all_recognition_results(page, page_size, search, status_list=status_list)
    else:
        pagination = RecognitionResultRepo.get_recognition_results_by_user_id(user_id, page, page_size, search, status_list=status_list)

    data = iPagenation(pagination)
    recognition_ids = [item.get('id') for item in data['items'] if item.get('id')]

    latest_node_map = {}
    if recognition_ids:
        latest_node_time_sq = db.session.query(
            SRecognitionNode.recognition_id.label('rid'),
            func.max(SRecognitionNode.create_time).label('max_ct')
        ).filter(
            SRecognitionNode.recognition_id.in_(recognition_ids)
        ).group_by(
            SRecognitionNode.recognition_id
        ).subquery()

        latest_nodes = db.session.query(
            SRecognitionNode.recognition_id,
            SRecognitionNode.node_type
        ).join(
            latest_node_time_sq,
            and_(
                SRecognitionNode.recognition_id == latest_node_time_sq.c.rid,
                SRecognitionNode.create_time == latest_node_time_sq.c.max_ct
            )
        ).all()

        for rid, node_type in latest_nodes:
            if rid not in latest_node_map:
                latest_node_map[rid] = node_type

    consumption_map = {}
    if recognition_ids:
        consumption_sums = db.session.query(
            SConsumption.recognition_id,
            func.sum(SConsumption.amount).label('amount_sum')
        ).filter(
            SConsumption.recognition_id.in_(recognition_ids)
        ).group_by(
            SConsumption.recognition_id
        ).all()

        for rid, amount_sum in consumption_sums:
            try:
                consumption_map[rid] = float(amount_sum or 0)
            except Exception:
                consumption_map[rid] = 0.0

    _items = []
    for item in data['items']:
        rid = item.get('id')
        _items.append({
            'id': item['id'],
            'image_no': item['image_no'],
            'image_url': item['image_url'],
            'thumbnail_url': item['thumbnail_url'],
            'algorithm_type': item['algorithm_type'],
            'create_time': item['create_time'].strftime('%Y-%m-%d %H:%M:%S') if item['create_time'] else None,
            "status": latest_node_map.get(rid, ''),
            "consumption": consumption_map.get(rid, 0.0),
        })
    data['items'] = _items
    return Success(data=data)


@api.route('/dashboard', methods=['GET'])
@login_required
def get_dashboard():
    user_id = g.user_id
    is_admin = (user_id == "view_way_admin_2026")

    now = datetime.now()
    start_day = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
    end_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    base_q = db.session.query(SRecognitionResult)
    if not is_admin:
        base_q = base_q.filter(SRecognitionResult.user_id == user_id)
    base_q = base_q.filter(SRecognitionResult.create_time >= start_day, SRecognitionResult.create_time <= end_day)

    recs = base_q.all()
    rec_ids = [r.id for r in recs]

    day_keys = []
    for i in range(7):
        d = (start_day + timedelta(days=i))
        day_keys.append(d.strftime('%m-%d'))

    count_map = {k: 0 for k in day_keys}
    for r in recs:
        k = r.create_time.strftime('%m-%d') if r.create_time else None
        if k in count_map:
            count_map[k] += 1

    cost_map = {k: 0.0 for k in day_keys}
    if rec_ids:
        down_rows = db.session.query(
            SConsumption.recognition_id,
            func.sum(SConsumption.amount).label('amt')
        ).filter(
            SConsumption.recognition_id.in_(rec_ids),
            SConsumption.status == 'down'
        ).group_by(SConsumption.recognition_id).all()

        down_map = {}
        for rid, amt in down_rows:
            try:
                down_map[rid] = float(amt or 0)
            except Exception:
                down_map[rid] = 0.0

        for r in recs:
            k = r.create_time.strftime('%m-%d') if r.create_time else None
            if k in cost_map:
                cost_map[k] += down_map.get(r.id, 0.0)

    trend = []
    for k in day_keys:
        trend.append({
            'day': k,
            'tasks': int(count_map.get(k, 0)),
            'cost': float(cost_map.get(k, 0.0))
        })

    alg_counter = {}
    for r in recs:
        ids = r.detect_alg if isinstance(r.detect_alg, list) else []
        for alg_item in ids:
            if not alg_item:
                continue
            alg_id = None
            if isinstance(alg_item, dict):
                alg_id = alg_item.get('id') or alg_item.get('alg_id') or alg_item.get('ai_asset_id')
            else:
                alg_id = str(alg_item)
            
            if alg_id:
                alg_counter[str(alg_id)] = alg_counter.get(str(alg_id), 0) + 1

    alg_ids = list(alg_counter.keys())
    name_map = {}
    if alg_ids:
        cfgs = db.session.query(SAIAssetConfig).filter(SAIAssetConfig.id.in_(alg_ids)).all()
        for c in cfgs:
            name_map[c.id] = c.ai_name

    total_alg = sum(alg_counter.values()) or 0
    usage_items = []
    for alg_id, cnt in sorted(alg_counter.items(), key=lambda x: x[1], reverse=True)[:5]:
        usage_items.append({
            'id': alg_id,
            'name': name_map.get(alg_id, alg_id),
            'count': int(cnt),
            'percent': int(round((cnt / total_alg) * 100)) if total_alg else 0
        })

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_q = db.session.query(SRecognitionResult)
    if not is_admin:
        today_q = today_q.filter(SRecognitionResult.user_id == user_id)
    today_q = today_q.filter(SRecognitionResult.create_time >= today_start).order_by(
        SRecognitionResult.create_time.desc()
    ).limit(10)
    today_recs = today_q.all()
    today_ids = [r.id for r in today_recs]

    today_cost_map = {}
    if today_ids:
        rows = db.session.query(SConsumption.recognition_id, func.sum(SConsumption.amount)).filter(
            SConsumption.recognition_id.in_(today_ids),
            SConsumption.status == 'down'
        ).group_by(SConsumption.recognition_id).all()
        for rid, amt in rows:
            try:
                today_cost_map[rid] = float(amt or 0)
            except Exception:
                today_cost_map[rid] = 0.0

    today_tasks = []
    for r in today_recs:
        first_alg = None
        if isinstance(r.detect_alg, list) and len(r.detect_alg) > 0:
            alg_item = r.detect_alg[0]
            if isinstance(alg_item, dict):
                first_alg = str(alg_item.get('id') or alg_item.get('alg_id') or alg_item.get('ai_asset_id') or '')
                # If the dict has a name, we could use it directly, but let's map it via name_map if possible
                if not first_alg and 'name' in alg_item:
                    first_alg = alg_item['name']
            else:
                first_alg = str(alg_item)
        
        algorithm_name = r.algorithm_type or ''
        if first_alg:
            # If first_alg is just a name and not an ID, name_map.get will return the name
            algorithm_name = name_map.get(first_alg, first_alg)
            
            # Check if the DB snapshot had the name
            if algorithm_name == first_alg and isinstance(r.detect_alg[0], dict) and 'name' in r.detect_alg[0]:
                algorithm_name = r.detect_alg[0]['name']

        today_tasks.append({
            'time': r.create_time.strftime('%H:%M') if r.create_time else '',
            'algorithm': algorithm_name,
            'images': 1,
            'latency': None,
            'status': '成功' if r.status in ['success', 'output'] else ('进行中' if r.status in ['waiting', 'processing'] else '失败'),
            'cost': float(today_cost_map.get(r.id, 0.0))
        })

    return Success(data={
        'trend': trend,
        'algorithm_usage': usage_items,
        'today_tasks': today_tasks
    })
