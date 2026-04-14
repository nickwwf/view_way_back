#!/usr/bin/python

import datetime
import decimal
import hashlib
import json

import numpy as np
from pandas._libs import NaTType


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, datetime.datetime):
            if isinstance(obj, NaTType):
                return None
            return obj.strftime(get_second_format())
        elif isinstance(obj, datetime.date):
            return obj.strftime(get_date_format())
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        elif hasattr(obj, 'keys') and hasattr(obj, '__getitem__'):
            return {key: obj[key] for key in obj.keys()}
        else:
            return super(NpEncoder, self).default(obj)


def get_second_format():
    return '%Y-%m-%d %H:%M:%S'


def get_minute_format():
    return '%Y-%m-%d %H:%M'


def get_date_format():
    return '%Y-%m-%d'


def get_month_format():
    return '%Y-%m'


def ntime():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def tadd(h=None, m=None, s=None):
    now = datetime.datetime.now()
    if h:
        time = now + datetime.timedelta(hours=h)
    elif m:
        time = now + datetime.timedelta(minutes=m)
    elif s:
        time = now + datetime.timedelta(seconds=s)
    return time.strftime('%Y-%m-%d %H:%M:%S')


def str_to_md5(parm_str):
    # 1、参数必须是utf8
    # 2、python3所有字符都是unicode形式，已经不存在unicode关键字
    # 3、python3 str 实质上就是unicode
    if isinstance(parm_str, str):
        # 如果是unicode先转utf-8
        parm_str = parm_str.encode("utf-8")
    m = hashlib.md5()
    m.update(parm_str)
    return m.hexdigest()


class f_str(str):

    def to_int(self):
        try:
            return int(self)
        except:
            return -1

    def to_datetime(self, date_str):
        try:
            return datetime.datetime.strptime(self, date_str)
        except:
            return None

    def to_list(self, sep):
        try:
            return self.split(sep=sep)
        except:
            return None


def time_to_minutes(time_str):
    """将时间字符串转换为分钟数"""
    hours, minutes = map(int, time_str.split(':'))
    return hours * 60 + minutes


def is_time_in_range(time_range_str, target_range_str="9:00-17:00"):
    """
    将时间转换为分钟数进行比较，更准确

    参数:
    time_range_str: 要检查的时间区间，格式如 "21:00-23:00"
    target_range_str: 目标时间区间，默认为 "9:00-17:00"

    返回:
    bool: 如果time_range完全在target_range内返回True，否则返回False
    """
    # 解析时间范围
    time_parts = time_range_str.split('-')
    target_parts = target_range_str.split('-')

    # 转换为分钟数
    time_start = time_to_minutes(time_parts[0])
    time_end = time_to_minutes(time_parts[1])
    target_start = time_to_minutes(target_parts[0])
    target_end = time_to_minutes(target_parts[1])

    # 检查是否完全在目标区间内
    return target_start <= time_start and time_end <= target_end


def are_all_times_in_range(time_list, start_time="9:00", end_time="17:00"):
    """
    判断时间数组内所有时间是否都在指定时间区间内

    参数:
    time_list: 时间数组，格式如 ["07:30", "08:30", "12:00"]
    start_time: 开始时间，默认为 "9:00"
    end_time: 结束时间，默认为 "17:00"

    返回:
    tuple: (是否全部在区间内, 不在区间内的时间列表)
    """
    start_minutes = time_to_minutes(start_time)
    end_minutes = time_to_minutes(end_time)

    not_in_range = []

    for time_str in time_list:
        time_minutes = time_to_minutes(time_str)

        # 检查时间是否在区间内 [start_time, end_time]
        if not (start_minutes <= time_minutes < end_minutes):
            not_in_range.append(time_str)

    return len(not_in_range) == 0, not_in_range
