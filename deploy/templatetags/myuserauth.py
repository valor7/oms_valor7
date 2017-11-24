#!/usr/bin/env python
# coding: utf8
'''
@Creator: valor7
@Email: valor7@163.com
@File: myuserauth.py
@Time: 2017/10/15 15:31
@desc:
'''

from django import template
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from userauth.models import User, UserGroup, Department
from deploy.models import SaltHost, SaltGroup, Project

register = template.Library()

def show_permissions(aid, perm_type):
    '''
    获取所有权限
    '''
    select_permissions_dict = {}
    permissions = Permission.objects.filter(
        Q(content_type__app_label__exact='asset') |
        Q(content_type__app_label__exact='deploy') |
        Q(content_type__app_label__exact='userperm')).values('pk', 'name')
    permissions_dict = {i['pk']:i['name'] for i in permissions}

    if aid and perm_type == 'user':
        user = User.objects.get(pk=aid)
        select_permissions_dict = {i['pk']: i['name'] for i in user.user_permissions.values('pk', 'name')}
        select_permissions_group_dict = {i['pk']: '%s（继承组）'%i['name'] for g in user.group.all() for i in g.permissions.values('pk', 'name')}
        select_permissions_dict = dict(select_permissions_dict, **select_permissions_group_dict)
    elif aid and perm_type == 'user_group':
        group = Group.objects.get(pk=aid)
        select_permissions_dict = {i['pk']:i['name'] for i in group.permissions.values('pk','name')}
    elif aid and perm_type == 'department':
        select_permissions_dict = {i['pk']:i['name'] for i in Department.objects.get(pk=aid).permissions.values('pk', 'name')}

    for i in select_permissions_dict:
        if i in permissions_dict:
            del permissions_dict[i]

    return {'permissions_dict':permissions_dict, 'select_permissions_dict':select_permissions_dict}

register.inclusion_tag('tag_permissions.html')(show_permissions)


def show_users(aid, value):
    '''
    获取用户
    '''

    select_users_dict = {}
    users_dict = {i['pk']: i['first_name'] for i in User.objects.values('pk', 'first_name')}

    if aid and value=='user_group':
        select_users_dict = {i['pk']:i['first_name'] for i in UserGroup.objects.get(pk=aid).user_group_set.values('pk', 'first_name')}
    elif aid and value=='department':
        # aid here is department name
        select_users_dict = {i['pk']:i['first_name'] for i in Department.objects.get(pk=aid).user_set.values('pk', 'first_name')}
    print select_users_dict
    for i in select_users_dict:
        if i in users_dict:
            del users_dict[i]

    return {'users_dict':users_dict, 'select_users_dict':select_users_dict}

register.inclusion_tag('tag_users.html')(show_users)


def show_user_groups(aid):
    '''
    获取用户组
    '''
    select_user_groups_dict = {}
    user_groups_dict = {i['pk']: i['group_name'] for i in UserGroup.objects.values('pk', 'group_name')}

    if aid:
        select_user_groups_dict = {i['pk']:i['group_name'] for i in User.objects.get(pk=aid).group.values('pk', 'group_name')}

    for i in select_user_groups_dict:
        if i in user_groups_dict:
            del user_groups_dict[i]

    return {'user_groups_dict':user_groups_dict, 'select_user_groups_dict':select_user_groups_dict}

register.inclusion_tag('tag_user_groups.html')(show_user_groups)


def show_department_saltgroups(aid):
    '''
    获取部门主机组
    :param aid:
    :return:
    '''
    select_groups_dict = {}
    groups = {i['pk']: i['nickname'] for i in SaltGroup.objects.values('pk', 'nickname')}

    if aid:
        select_groups_dict = {i['pk']: i['nickname'] for i in SaltGroup.objects.filter(department=aid).values('pk', 'nickname')}

    for i in select_groups_dict:
        if i in groups:
            del groups[i]

    return {'groups':groups, 'select_groups_dict':select_groups_dict}

register.inclusion_tag('tag_department_groups.html')(show_department_saltgroups)


def show_minions(aid, arg):
    '''
    获取用户组或Salt分组主机
    :param aid:
    :return:
    '''
    select_minions_dict = {}
    minions = {i['pk']: i['hostname'] for i in SaltHost.objects.filter(status=True).values('pk', 'hostname')}

    if aid and arg == 'user_group':
        select_minions_dict = {i['pk']:i['hostname'] for i in SaltHost.objects.filter(user_group=aid).values('pk', 'hostname')}
    elif aid and arg == 'saltgroup':
        select_minions_dict = {i['pk']:i['hostname'] for i in SaltGroup.objects.get(pk=aid).minions.values('pk', 'hostname')}

    for i in select_minions_dict:
        if i in minions:
            del minions[i]

    return {'minions':sorted(minions.items()), 'select_minions_dict':sorted(select_minions_dict.items())}
register.inclusion_tag('tag_minions.html')(show_minions)


def show_host_groups(aid, type):
    '''
    获取Salt分组
    :param aid:
    :return:
    '''
    select_host_groups_dict = {}
    host_groups = {i['pk']: i['nickname'] for i in SaltGroup.objects.values('pk', 'nickname')}

    if type == 'project' and aid:
        select_host_groups_dict = {i['pk']: i['nickname'] for i in
                                   Project.objects.get(pk=aid).salt_group.values('pk', 'nickname')}
    elif aid:
        select_host_groups_dict = {i['pk']: i['nickname'] for i in
                                   SaltGroup.objects.filter(user_group=aid).values('pk', 'nickname')}

    for i in select_host_groups_dict:
        if i in host_groups:
            del host_groups[i]

    return {'host_groups':sorted(host_groups.items()), 'select_host_groups_dict':sorted(select_host_groups_dict.items())}
register.inclusion_tag('tag_groups.html')(show_host_groups)


def show_group_minions(aid):
    '''
    获取主机和主机组
    :param aid:
    :return:
    '''
    select_minions_dict = {}
    minions = {i: i.minions.values('hostname') for i in SaltGroup.objects.all()}

    if aid:
        select_minions_dict = {i['pk']: i['hostname'] for i in
                               SaltGroup.objects.filter(user_group=aid).minions.values('pk', 'hostname')}

    return {'minions':sorted(minions.items()), 'select_minions_dict':sorted(select_minions_dict.items())}
register.inclusion_tag('tag_group_minions.html')(show_group_minions)


def show_group_departments(aid):
    '''
    获取部门
    :param aid:
    :return:
    '''
    select_departments_dict = {}
    departments = {i['pk']: i['name'] for i in Department.objects.values('pk', 'name')}

    if aid:
        select_departments_dict = {i['pk']: i['name'] for i in Group.objects.get(pk=aid).department_group_set.values('pk', 'name')}
    print select_departments_dict
    for i in select_departments_dict:
        if i in departments:
            del departments[i]

    return {'departments':sorted(departments.items()), 'select_departments_dict':sorted(select_departments_dict.items())}

register.inclusion_tag('tag_group_departments.html')(show_group_departments)

