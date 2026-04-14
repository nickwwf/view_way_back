#!/usr/bin/python
# -*- coding:utf-8 -*-

'''
日志模块
'''
import os
import pathlib

import loguru
from datetime import datetime
from functools import wraps
from app.env import base_path
# 单个类的装饰器

def singleton(cls):
    _instance = {}
    @wraps(cls)
    def wrapper(*args,**kwargs):
        if cls not in _instance:
            _instance[cls] = cls(*args,**kwargs)
        return _instance[cls]
    # 返回一个类
    return wrapper


class Log(object):
    """
    飞视日志类：
    1. 日志文件默认通过按照url_path进行分类,默认路径：
    $HOME/{project_name}/logs/{url_path}
    2. url_path格式如下：/{}/{}
    """

    def __init__(self,url_path=None,log_name='fsee'):
        self.url_path = self.get_url_path(url_path)
        self.log_name = self.get_log_name(self.url_path)
        self.file_name = self.get_file_name(self.url_path)
        self.log_add()

    def get_file_name(self,url_path):
        return url_path.split('/')[-1]

    def get_log_name(self,log_path):
        names = log_path.split('/')
        return '_'.join(names)

    def get_url_path(self,log_path):
        if not log_path:
            return 'fsee/fsee'
        if log_path[0] == '/':
            log_path = log_path[1:]
        return log_path

    @property
    def log_file(self):
        path = base_path
        return path/'logs'

    @property
    def log_path(self):
        log_path_file = self.log_file/self.url_path
        if not log_path_file.exists():
            os.makedirs(log_path_file)
        log_path = self.log_file/f"{self.url_path}/{self.file_name}.log"
        return log_path

    @property
    def error_path(self):
        log_path_file = self.log_file/self.url_path
        if not log_path_file.exists():
            os.makedirs(log_path_file)
        log_path = self.log_file/f"{self.url_path}/{self.file_name}.error"
        return log_path


    def log_add(self):
        # TODO: 优化日志文件
        loguru.logger.add(
            self.log_path,rotation="00:00",retention="1 year",
            encoding="utf-8",enqueue=True,
            filter=lambda record: record["extra"].get("name") == self.log_name,
        )

        loguru.logger.add(
            self.error_path, rotation="00:00", retention="1 year",
            encoding="utf-8", enqueue=True,
            filter=lambda record: record["extra"].get("name") == self.log_name and \
                                  record["level"].name == "ERROR",
        )

    @property
    def get_loggers(self):
        return loguru.logger.bind(name=self.log_name)



#log = Log(log_name='fsee').get_loggers





