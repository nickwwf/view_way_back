# coding: utf-8
from datetime import datetime, timedelta

from sqlalchemy import func

from app.models.s_consumption import SConsumption
from app.models.s_ai_asset_config import SAIAssetConfig
from app.models.s_user import SUser
from app.models.s_recognition_result import SRecognitionResult
from app.models.base import db
from app.libs.error_code import ServerError

class ConsumptionRepo:
    @staticmethod
    def _parse_dt(value, end_of_day=False):
        if not value:
            return None
        s = str(value).strip()
        if not s:
            return None
        fmts = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d']
        for fmt in fmts:
            try:
                dt = datetime.strptime(s, fmt)
                if fmt == '%Y-%m-%d' and end_of_day:
                    dt = dt + timedelta(days=1) - timedelta(seconds=1)
                return dt
            except Exception:
                continue
        return None

    @staticmethod
    def _normalize_detect_alg(detect_alg):
        if detect_alg is None:
            return []
        if isinstance(detect_alg, (list, tuple)):
            return list(detect_alg)
        return [detect_alg]

    @staticmethod
    def calc_amount(detect_alg, session=None) -> float:
        items = ConsumptionRepo._normalize_detect_alg(detect_alg)
        if not items:
            return 0.0

        alg_ids = []
        price_sum = 0.0
        for item in items:
            if isinstance(item, str):
                alg_ids.append(item)
            elif isinstance(item, dict):
                item_id = item.get('id') or item.get('alg_id') or item.get('ai_asset_id')
                if item_id:
                    alg_ids.append(item_id)
                    continue
                try:
                    price_sum += float(item.get('price', 0) or 0)
                except Exception:
                    continue
            else:
                continue

        if alg_ids:
            query = (session or db.session).query(SAIAssetConfig).filter(
                SAIAssetConfig.id.in_(alg_ids),
                SAIAssetConfig.is_del == 0
            )
            configs = query.all()
            for cfg in configs:
                try:
                    price_sum += float(cfg.price or 0)
                except Exception:
                    continue

        return float(price_sum)

    @staticmethod
    def create_pre_consumption(user_id, recognition_id, detect_alg=None, amount=None, consumption_type='image_recognition', description=None, session=None, auto_commit=True):
        if not user_id or not recognition_id:
            raise ServerError(msg='user_id and recognition_id are required')

        amt = float(amount) if amount is not None else ConsumptionRepo.calc_amount(detect_alg, session=session)
        if amt < 0:
            amt = 0.0

        def _apply(sess):
            existing = (sess.query(SConsumption)
                        .filter_by(recognition_id=recognition_id)
                        .order_by(SConsumption.create_time.desc())
                        .first())
            if existing:
                return existing

            user = sess.query(SUser).filter_by(id=user_id).with_for_update().first()
            if user and (user.balance or 0) < amt:
                raise ServerError(msg='Insufficient balance')

            consumption_obj = SConsumption()
            consumption_obj.user_id = user_id
            consumption_obj.recognition_id = recognition_id
            consumption_obj.amount = amt
            consumption_obj.consumption_type = consumption_type
            consumption_obj.description = description
            consumption_obj.status = 'pre'
            sess.add(consumption_obj)

            if user:
                user.balance = (user.balance or 0) - amt
                sess.add(user)

            sess.flush()
            return consumption_obj

        if session is not None:
            obj = _apply(session)
            if auto_commit:
                session.commit()
            return obj

        with db.auto_commit():
            return _apply(db.session)

    @staticmethod
    def mark_down(recognition_id, session=None, auto_commit=True):
        if not recognition_id:
            return None

        def _apply(sess):
            consumption = sess.query(SConsumption).filter_by(recognition_id=recognition_id).order_by(SConsumption.create_time.desc()).first()
            if not consumption:
                return None
            if consumption.status == 'down':
                return consumption
            if consumption.status == 'back':
                return consumption
            if consumption.status != 'pre':
                return consumption
            consumption.status = 'down'
            sess.add(consumption)
            return consumption

        if session is not None:
            obj = _apply(session)
            if auto_commit:
                session.commit()
            return obj

        with db.auto_commit():
            return _apply(db.session)

    @staticmethod
    def mark_back(recognition_id, session=None, auto_commit=True):
        if not recognition_id:
            return None

        def _apply(sess):
            consumption = sess.query(SConsumption).filter_by(recognition_id=recognition_id).order_by(SConsumption.create_time.desc()).first()
            if not consumption:
                return None
            if consumption.status == 'back':
                return consumption
            if consumption.status != 'pre':
                return consumption

            user = sess.query(SUser).filter_by(id=consumption.user_id).with_for_update().first()
            refund_amount = float(consumption.amount or 0)
            if user and refund_amount > 0:
                user.balance = (user.balance or 0) + refund_amount
                sess.add(user)

            consumption.status = 'back'
            sess.add(consumption)
            sess.flush()
            return consumption

        if session is not None:
            obj = _apply(session)
            if auto_commit:
                session.commit()
            return obj

        with db.auto_commit():
            return _apply(db.session)
    
    @staticmethod
    def get_consumption_by_id(consumption_id):
        return SConsumption.query.filter_by(id=consumption_id).first()
    
    @staticmethod
    def get_consumption_list(user_id, page=1, size=10, filters=None):
        query = SConsumption.query.filter_by(user_id=user_id)
        
        if filters:
            if 'consumption_type' in filters and filters['consumption_type']:
                query = query.filter(SConsumption.consumption_type == filters['consumption_type'])
            if 'status' in filters and filters['status']:
                query = query.filter(SConsumption.status == filters['status'])
            if 'start_time' in filters and filters['start_time']:
                start_dt = ConsumptionRepo._parse_dt(filters['start_time'])
                if start_dt:
                    query = query.filter(SConsumption.create_time >= start_dt)
            if 'end_time' in filters and filters['end_time']:
                end_dt = ConsumptionRepo._parse_dt(filters['end_time'], end_of_day=True)
                if end_dt:
                    query = query.filter(SConsumption.create_time <= end_dt)
        
        pagination = query.order_by(SConsumption.create_time.desc()).paginate(
            page=page,
            per_page=size,
            error_out=False
        )
        
        consumption_list = []
        for consumption in pagination.items:
            consumption_list.append({
                'id': consumption.id,
                'user_id': consumption.user_id,
                'recognition_id': consumption.recognition_id,
                'amount': consumption.amount,
                'consumption_type': consumption.consumption_type,
                'description': consumption.description,
                'status': consumption.status,
                'create_time': consumption.create_time.strftime('%Y-%m-%d %H:%M:%S') if consumption.create_time else None
            })
        
        return consumption_list, pagination.total

    @staticmethod
    def get_deduct_consumption_list(user_id, page=1, size=10, filters=None):
        query = (db.session.query(SConsumption, SRecognitionResult)
                 .outerjoin(SRecognitionResult, SRecognitionResult.id == SConsumption.recognition_id)
                 .filter(SConsumption.user_id == user_id))

        if filters:
            if filters.get('consumption_type'):
                query = query.filter(SConsumption.consumption_type == filters['consumption_type'])

            status_raw = str(filters.get('status') or '').strip()
            if status_raw:
                status_list = [s.strip() for s in status_raw.split(',') if s.strip()]
                if status_list:
                    query = query.filter(SConsumption.status.in_(status_list))
            else:
                query = query.filter(SConsumption.status.in_(['pre', 'down', 'back']))

            start_dt = ConsumptionRepo._parse_dt(filters.get('start_time'))
            if start_dt:
                query = query.filter(SConsumption.create_time >= start_dt)

            end_dt = ConsumptionRepo._parse_dt(filters.get('end_time'), end_of_day=True)
            if end_dt:
                query = query.filter(SConsumption.create_time <= end_dt)

            keyword = str(filters.get('search') or '').strip()
            if keyword:
                query = query.filter(
                    (SConsumption.description.like(f"%{keyword}%")) |
                    (SRecognitionResult.image_no.like(f"%{keyword}%"))
                )
        else:
            query = query.filter(SConsumption.status.in_(['pre', 'down', 'back']))

        total = query.count()

        pre_amount = 0.0
        down_amount = 0.0
        back_amount = 0.0
        rows_sum = query.with_entities(SConsumption.status, func.sum(SConsumption.amount)).group_by(SConsumption.status).all()
        for st, amt in rows_sum:
            try:
                v = float(amt or 0)
            except Exception:
                v = 0.0
            if st == 'pre':
                pre_amount = v
            elif st == 'down':
                down_amount = v
            elif st == 'back':
                back_amount = v
        net_amount = float(down_amount)
        deducted_amount = float(pre_amount + down_amount)

        rows = (query.order_by(SConsumption.create_time.desc())
                .offset((page - 1) * size)
                .limit(size)
                .all())

        items = []
        for c, r in rows:
            items.append({
                'id': c.id,
                'recognition_id': c.recognition_id,
                'amount': float(c.amount or 0),
                'consumption_type': c.consumption_type,
                'description': c.description,
                'status': c.status,
                'create_time': c.create_time.strftime('%Y-%m-%d %H:%M:%S') if c.create_time else None,
                'recognition': {
                    'id': r.id if r else None,
                    'image_no': r.image_no if r else None,
                    'thumbnail_url': r.thumbnail_url if r else None,
                    'image_url': r.image_url if r else None,
                    'algorithm_type': r.algorithm_type if r else None,
                    'status': r.status if r else None
                }
            })

        user = db.session.query(SUser).filter_by(id=user_id).first()
        balance = float(user.balance or 0) if user else 0.0

        return items, total, {
            'count': total,
            'pre_amount': float(pre_amount),
            'down_amount': float(down_amount),
            'back_amount': float(back_amount),
            'net_amount': float(net_amount),
            'deducted_amount': float(deducted_amount),
            'balance': float(balance)
        }
    
    @staticmethod
    def get_user_balance(user_id):
        user = SUser.query.filter_by(id=user_id).first()
        return user.balance if user else 0.0
    
    @staticmethod
    def update_user_balance(user_id, amount):
        user = None
        with db.auto_commit():
            user = db.session.query(SUser).filter_by(id=user_id).with_for_update().first()
            if not user:
                return None
            user.balance = float(user.balance or 0) + float(amount or 0)
            db.session.add(user)
            db.session.flush()
        return user
