#!/usr/bin/python
# -*- coding:utf-8 -*-
#########################################
# > File Name: wt_form.py
# > Author: zszaa
# > Mail: zszaa_0805@163.com
# > Created Time: 2023-03-21 14:17:30
##########################################


from wtforms import Form
from flask import request


class QueryForm(Form):

    def __init__(self):
        #data = request.get_json()
        args = request.args.to_dict()
        super(QueryForm, self).__init__(**args)

    def validate_for_api(self):
        valid = super(QueryForm, self).validate()
        print(valid,'aaaaaaaaaaa')
        if not valid:
            raise Exception(msg=self.errors)
        return True


