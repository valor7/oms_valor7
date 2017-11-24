#!/usr/bin/env python
# coding: utf8
'''
@Creator: valor7
@Email: valor7@163.com
@File: models.py.py
@Time: 2017/10/15 16:06
@desc:
'''

from __future__ import unicode_literals

from django.db import models
from django.contrib import auth
from django.contrib.auth.models import AbstractUser, Group, Permission, PermissionsMixin

from django.core.validators import RegexValidator

from userperm.models import UserCommand, UserDirectory


class Department(Group):
    deptname = models.CharField(max_length=20, verbose_name=u'部门')
    parent = models.ForeignKey('self', blank=True, null=True, related_name='department_children', verbose_name=u'上级部门')
    level = models.PositiveIntegerField(default=1, verbose_name=u'部门级别')

    def clean(self):
        self.name = self.deptname

    def __str__(self):
        return self.deptname

    class Meta:
        default_permissions = ()
        permissions = (
            ('view_department', u'查看部门'),
            ('edit_department', u'管理部门'),
        )
        verbose_name = u'部门'
        verbose_name_plural = u'部门管理'

class UserGroup(Group):
    group_name = models.CharField(max_length=80, unique=True, verbose_name=u'用户组')
    command = models.ManyToManyField(UserCommand, related_name='group_command_set', verbose_name=u'用户组命令')
    directory = models.ManyToManyField(UserDirectory, related_name='group_directory_set', verbose_name=u'用户组目录')
    comment = models.TextField(blank=True, null=True, verbose_name=u'备注')

    def clean(self):
        self.name = self.group_name

    def __unicode__(self):
        return self.group_name

    class Meta:
        default_permissions = ()
        verbose_name = u'用户组'
        verbose_name_plural = u'用户组管理'

class User(AbstractUser):
    USER_ROLE_CHOICES = (
        ('SU', u'超级管理员'),
        ('GA', u'组管理员'),
        ('CU', u'普通用户')
    )
    qq = models.CharField(max_length=16, blank=True, verbose_name=u'QQ', validators=[
        RegexValidator(regex='^[^0]\d{4,15}$', message=u'请输入正确的QQ号')])
    mobile = models.CharField(max_length=30, blank=True, verbose_name=u'联系电话', validators=[
        RegexValidator(regex='^[^0]\d{6,7}$|^[1]\d{10}$', message=u'请输入正确的电话或手机号码', code=u'号码错误')],
                              error_messages={'required': u'联系电话不能为空'})
    position = models.CharField(max_length=20, blank=True, verbose_name=u'职位')
    role = models.CharField(max_length=2, choices=USER_ROLE_CHOICES, default='CU')
    group = models.ManyToManyField(UserGroup, related_name='user_group_set', verbose_name=u'用户属组')

    def __unicode__(self):
        return self.username

    class Meta:
        default_permissions = ()
        permissions = (
            ('view_user', u'查看用户'),
            ('edit_user', u'管理用户'),
        )
        verbose_name = u'用户'
        verbose_name_plural = u'用户管理'




class AdminGroup(models.Model):
    user = models.ForeignKey(User)
    group = models.ForeignKey(UserGroup)

    def __unicode__(self):
        return '%s: %s' %(self.user.username, self.group.group_name)

    class Meta:
        default_permissions = ()
        verbose_name = u'管理员组'
        verbose_name_plural = u'管理员组管理'

