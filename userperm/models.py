#!/usr/bin/env python
# coding: utf8
'''
@Creator: valor7
@Email: valor7@163.com
@File: models.py
@Time: 2017/10/15 16:05
@desc:
'''

from __future__ import unicode_literals

from django.db import models
#from userauth.models import UserGroup
# Create your models here.

class Message(models.Model):
    user = models.CharField(max_length=244, verbose_name=u'用户')
    audit_time = models.DateTimeField(auto_now_add=True, verbose_name=u'时间')
    type = models.CharField(max_length=10, verbose_name=u'类型')
    action = models.CharField(max_length=20, verbose_name=u'动作')
    action_ip = models.CharField(max_length=15, verbose_name=u'用户IP')
    content = models.TextField(verbose_name=u'内容')

    class Meta:
        default_permissions = ()
        permissions = (
            ("view_message", u"查看操作记录"),
            ("edit_message", u"管理操作记录"),
        )
        ordering = ['-audit_time']
        verbose_name = u'审计信息'
        verbose_name_plural = u'审计信息管理'

class UserCommand(models.Model):
    name = models.CharField(
        max_length=80,
        unique=True,
        verbose_name=u'命令别名')
    command = models.TextField(blank=True, verbose_name=u'系统命令')
    is_allow = models.BooleanField(default=True, verbose_name=u'状态')

    def __str__(self):
        return self.name

    class Meta:
        default_permissions = ()
        permissions = (
            ("edit_remote_permission", u"管理远程权限"),
        )
        verbose_name = u'远程命令'
        verbose_name_plural = u'远程命令管理'

class UserDirectory(models.Model):
    name = models.CharField(max_length=80, unique=True, verbose_name=u'目录别名')
    directory = models.TextField(blank=True, verbose_name=u'系统目录')
    is_allow = models.BooleanField(default=True, verbose_name=u'状态')

    def __str__(self):
        return self.name
    
    class Meta:
        default_permissions = ()
        verbose_name = u'远程目录'
        verbose_name_plural = u'远程目录管理'

