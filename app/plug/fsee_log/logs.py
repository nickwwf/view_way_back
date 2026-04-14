#!/usr/bin/python
# -*- coding:utf-8 -*-



from flask import request
from app.plug.fsee_log.log import Log


class FseeLogs(object):

    def __init__(self,log_name=None):
        self.logs = dict()
        self.log_name = log_name
        self.init_path = '/fsee/fsee'

    def get_log_name(self,path):
        log_name = path[1:].replace('/','_')
        return log_name

    def get_log_path(self):
        try:
            path = request.path
        except Exception as e:
            path = self.init_path
        return path

    @property
    def logger(self,):
        url_path = self.get_log_path()
        name = self.get_log_name(url_path)
        if name not in self.logs.keys():
            self.logs[name] = Log(url_path=url_path).get_loggers
        return self.logs[name]



