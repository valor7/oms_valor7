#!/usr/bin/env python
# coding: utf8
'''
@Creator: valor7
@Email: valor7@163.com
@File: myinclusion.py
@Time: 2017/10/15 15:32
@desc:
'''

from django import template
from django.db.models import Q

from deploy.models import *
from userauth.models import *

register = template.Library()


def show_single_minions(pk, user_type):
    '''
    文件回滚中单项显示主机列表
    '''
    tgt_list = []
    if user_type:
        tgt_list = [i['hostname'] for i in SaltHost.objects.filter(status=True).values('hostname')]
    else:
        tgt_list = [i['hostname'] for d in User.objects.get(pk=pk).department.all() for i in
                    d.host_department_set.values('hostname')]
    return {'tgt_list': sorted(list(set(tgt_list)))}

register.inclusion_tag('tag_single_minions.html')(show_single_minions)


def show_groups(pk, user_type):
    '''
    远程命令、模块部署及文件管理中显示所有分组
    '''
    group_dict = {}
    if user_type:
        group_dict = {i['groupname']:i['nickname'] for i in SaltGroup.objects.values('groupname', 'nickname')}
    else:
        d = User.objects.get(pk=pk).department
        group_dict = {i['groupname']:i['nickname'] for d in User.objects.get(pk=pk).department.all()
                      for i in d.saltgroup_department_set.values('groupname', 'nickname')}

    return {'group_dict':sorted(list(set(group_dict.items())))}

register.inclusion_tag('tag_user_departments.html')(show_groups)


def show_modules(u, user_type):
    '''
    模块部署中显示所有模块
    '''
    if user_type:
        module_list = ModuleUpload.objects.all()
    else:
        # 获取用户创建或公开模块
        module_visible_list = [{'pk': i.pk, 'name': i.name, 'module': i.module, 'remark': i.remark}
                               for i in ModuleUpload.objects.filter(Q(user=u) | Q(visible=2))]
        # 获取用户组模块
        module_user_group_list = [{'pk': i.pk, 'name': i.name, 'module': i.module, 'remark': i.remark}
                                  for g in User.objects.get(pk=u.pk).group.all() for i in
                                  ModuleUpload.objects.filter(user_group=g)]
        # 合并list
        module_list = module_visible_list + [i for i in module_user_group_list if i not in module_visible_list]
    return {'module_list': module_list}

register.inclusion_tag('tag_modules.html')(show_modules)


def show_user_group_minions(pk, user_type, list_type):
    '''
    远程命令、模块部署及文件上传中显示主机列表
    '''
    if user_type:
        tgt_list = [i['hostname'] for i in SaltHost.objects.filter(status=True).values('hostname')]
    else:
        tgt_list = [i['hostname'] for g in User.objects.get(pk=pk).group.all() for i in
                    SaltHost.objects.filter(user_group=g).values('hostname')]
    return {'tgt_list':sorted(list(set(tgt_list))), 'list_type':list_type}

register.inclusion_tag('tag_user_group_minions.html')(show_user_group_minions)


def show_user_group_groups(pk, user_type):
    '''
    远程命令、模块部署及文件管理中显示用户分组
    '''
    group_dict = {}
    if user_type:
        group_dict = {i['groupname']:i['nickname'] for i in SaltGroup.objects.values('groupname', 'nickname')}
    else:
        group_dict = {i['groupname']:i['nickname'] for g in User.objects.get(pk=pk).group.all()
                      for i in SaltGroup.objects.filter(user_group=g).values('groupname', 'nickname')}

    return {'group_dict':sorted(list(set(group_dict.items())))}

register.inclusion_tag('tag_user_group_groups.html')(show_user_group_groups)

