#!/usr/bin/env python
# coding: utf8
'''
@Creator: valor7
@Email: valor7@163.com
@File: myfilter.py
@Time: 2017/10/15 15:32
@desc:
'''

from django import template
from django.contrib.auth.models import Group
from userauth.models import User, Department
from django.db.models import Q
from django.shortcuts import get_object_or_404
from deploy.models import SaltGroup

register = template.Library()

@register.filter(name='add_class')
def add_class(value, arg):
    return value.as_widget(attrs={'class': arg, 'required':'required'})

@register.filter(name='group_minions')
def minions(value):
    '''
    分组列表中显示所有主机
    '''

    try:
        group_minions = value.minions.all()
        return group_minions
    except:
        return ''

@register.filter(name='group_users')
def all_users(group):
    '''
    分组列表中显示所有主机
    '''

    try:
        #all_users = group.user_set.all()
        all_users = User.objects.filter(group=group)
        return all_users
    except:
        return ''

@register.filter(name='department_users')
def all_department_users(pk):
    '''
    部门所有用户
    '''

    try:
        all_department_users = Department.objects.get(pk=pk).user_set.all()
        return all_department_users
    except:
        return ''

@register.filter(name='user_departments')
def user_departments(user, level):
    '''
    用户所属部门（组）
    '''

    try:
        #user = User.objects.get(pk=pk)
        if level == "1":
            department = {i.id:i.deptname for i in user.department.filter(level=1)}
        else:
            department = {i.id:i.deptname for i in user.department.filter(~Q(level=1))}
        return sorted(department.items())
    except:
        return ''

@register.filter(name='user_groups')
def all_user_groups(pk):
    '''
    用户所属组
    '''

    try:
        user_group = [i.name for i in Group.objects.filter(user=pk)]
        return user_group
    except:
        return ''

@register.filter(name='department_subs')
def all_dept_subs(pk):
    '''
    子部门
    '''
    try:
        all_depts = ["<li>%s</li>"%i.deptname for i in Department.objects.filter(parent_id=pk)]
        return all_depts
    except:
        return ''

@register.filter(name='getNextDept')
def all_dept_node(pid):
    '''
    部门节点
    :param pk:
    :return:
    '''
    try:
        return Department.objects.filter(parent_id=pid).values('id', 'deptname', 'parent_id')
    except:
        return None

@register.filter(name='department_level')
def department_display(level):
    try:
        return 60 * (int(level) - 1)
    except:
        return ''

@register.filter(name='is_super')
def user_is_super(pk):
    '''
    是否为超级用户
    '''
    if pk:
        return User.objects.get(pk=pk).is_superuser
    else:
        return None

@register.filter(name='str_split')
def show_str(value, arg):
    '''
    分割权限控制中远程命令、远程目录列表
    '''
    if value:
        str_list = value.split(arg)
        return str_list
    else:
        return ''

@register.filter(name='list_item')
def show_item(value, arg):
    '''
    获取列表中指定项
    '''
    if value:
        return value[arg]
    else:
        return ''

