#!/usr/bin/python
# -*- coding:utf-8 -*-


"""常用的报错信息"""

class ErrorMsg:
    # 只适用于marshmallow的验证
    name_null = {'required': '用户不能为空!'}
    value_null = {'required': '参数不能为空!'}
    name_exist = {'required': '该用户名已存在!'}
    name_not_exist = {'required': '该用户名不存在!'}
    tel_null = {'required': '手机号不能为空!'}
    dept_null = {'required': '传入部门不能为空!'}
    org_null = {'required': '传入组织能为空!'}
    dept_not_exist = {'required': '传入部门不存在!'}
    id_not_exist = {'required': '传入ID值不存在!'}
    role_null = {'required': '传入角色不能为空!'}
    role_not_exist = {'required': '传入角色不存在!'}
    type_error = {'invalid': '传入类型不正确!'}
    file_null = {'required': '文件不存在!'}
    code_null = {'required': '验证码不能为空!'}
