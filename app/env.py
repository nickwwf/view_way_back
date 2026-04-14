#!/usr/bin/python
# -*- coding:utf-8 -*-
#########################################
# > File Name: config.py
# > Author: zszaa
# > Mail: zszaa_0805@163.com
# > Created Time: 2022-05-09 09:33:05
##########################################


import os
from pathlib import Path
import sys

'''
获取当前项目的环境
dev: 开发
test: 测试
prod: 生产
'''

class Env(object):

    def __init__(self,path=None):
        self.path = path

    @property
    def env_path(self):
        real_path = Path(
            os.path.split(os.path.realpath(__file__))[0]
        ).parent
        config_dir = self.path or real_path
        if os.path.exists(Path(config_dir)/'.flaskenv'):
            return config_dir/'.flaskenv'
        return None

    def get_env(self):
        if self.env_path:
            env = self.conf2py(self.env_path)
            return env
        return {
            "FLASK_CONFIG":"dev"
        }

    def conf2py(self,config_file):
        content,dic ={},{}
        with open(config_file, 'r') as f:
            a = exec(f.read(), content)
            for key,item in content.items():
                if key not in content['__builtins__'] and \
                   key != '__builtins__':
                    dic[key] = item
        return dic


def load_env(env_path=None):
    env = Env(env_path)
    return env.get_env()


class Config(object):

    def __init__(self,path=None):
        self.path = path
        self.env = load_env(path)

    @property
    def config_path(self):
        real_path = os.path.split(os.path.realpath(__file__))[0]
        config_dir = self.path or Path(real_path)
        return config_dir/'config'/f"{self.env['FLASK_CONFIG']}.py"

    def load(self,):
        scope,dic = {},{}
        with open(self.config_path,'r',encoding="utf-8",) as f:
            exec(f.read(),scope)
            for key,item in scope.items():
                if key not in scope['__builtins__'] and \
                        key != '__builtins__':
                    dic[key] = item
            return dic

load_conf = Config().load()


base_path = Path(os.path.split(os.path.realpath(__file__))[0]).parent
