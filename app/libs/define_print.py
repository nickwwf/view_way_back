#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author  : Administrator
# @Time    : 2026/3/10 9:03
# @File    : define_print.py
# @Software: PyCharm


class DefinePrint:
    def __init__(self, name):
        self.name = name
        self.mound = []

    # 自定义装饰器
    def route(self, rule, **options):
        def decorator(f):
            self.mound.append((f, rule, options))
            return f

        return decorator

    def register(self, bp, url_prefix=None):
        if url_prefix is None:
            url_prefix = '/' + self.name
        # 将视图注册到蓝图中
        for f, rule, options in self.mound:
            # 将 endpoint 定义为 模块名+函数名
            endpoint = self.name + '>>' + options.pop('endpoint', f.__name__)
            bp.add_url_rule(url_prefix + rule, endpoint, f, **options)
