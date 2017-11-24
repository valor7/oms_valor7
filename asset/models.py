#!/usr/bin/env python
# coding: utf8
'''
@Creator: valor7
@Email: valor7@163.com
@File: models.py
@Time: 2017/10/15 15:34
@desc:
'''

from __future__ import unicode_literals

from django.db import models

from django.core.validators import RegexValidator

# Create your models here.
class ServerAsset(models.Model):
    nodename = models.CharField(max_length=50, unique=True, default=None, verbose_name=u'Salt主机')
    hostname = models.CharField(max_length=50, unique=True, verbose_name=u'主机名')
    manufacturer = models.CharField(max_length=20, blank=True, verbose_name=u'厂商')
    productname = models.CharField(max_length=100, blank=True, verbose_name=u'型号')
    sn = models.CharField(max_length=20, blank=True, verbose_name=u'序列号')
    cpu_model = models.CharField(max_length=100, blank=True, verbose_name=u'CPU型号')
    cpu_nums = models.PositiveSmallIntegerField(verbose_name=u'CPU线程')
    memory = models.CharField(max_length=20, verbose_name=u'内存')
    disk = models.TextField(blank=True, verbose_name=u'硬盘')
    network = models.TextField(blank=True, verbose_name=u'网络接口')
    os = models.CharField(max_length=200, blank=True, verbose_name=u'操作系统')
    virtual = models.CharField(max_length=20, blank=True, verbose_name=u'虚拟化')
    kernel = models.CharField(max_length=200, blank=True, verbose_name=u'内核')
    shell = models.CharField(max_length=10, blank=True, verbose_name=u'Shell')
    zmqversion = models.CharField(max_length=10, blank=True, verbose_name=u'ZeroMQ')
    saltversion = models.CharField(max_length=10, blank=True, verbose_name=u'Salt版本')
    locale = models.CharField(max_length=200, blank=True, verbose_name=u'编码')
    selinux = models.CharField(max_length=50, blank=True, verbose_name=u'Selinux')
    idc = models.CharField(max_length=50, blank=True, verbose_name=u'机房')

    def __unicode__(self):
        return self.hostname

    class Meta:
        default_permissions = ()
        permissions = (
            ("view_asset", u"查看资产"),
            ("edit_asset", u"管理资产"),
        )
        verbose_name = u'主机资产信息'
        verbose_name_plural = u'主机资产信息管理'


class IdcAsset(models.Model):
    idc_name = models.CharField(max_length=20, verbose_name=u'机房名称')
    idc_type = models.CharField(max_length=20, blank=True, verbose_name=u'机房类型')
    idc_location = models.CharField(max_length=100, verbose_name=u'机房位置')
    contract_date = models.CharField(max_length=30, verbose_name=u'合同时间')
    idc_contacts = models.CharField(max_length=30, verbose_name=u'联系电话', validators=[
        RegexValidator(regex='^[^0]\d{6,7}$|^[1]\d{10}$', message='请输入正确的电话或手机号码', code='号码错误')],
                                    error_messages={'required': u'联系电话不能为空'})
    remark = models.TextField(max_length=255, blank=True, verbose_name=u'备注', default='')

    def __unicode__(self):
        return self.idc_name

    class Meta:
        default_permissions = ()
        verbose_name = u'IDC资产信息'
        verbose_name_plural = u'IDC资产信息管理'

class Provinces(models.Model):
    provinceid = models.CharField(max_length=20, unique=True, verbose_name=u'省份代码')
    province = models.CharField(max_length=50, verbose_name=u'省份')

    def __unicode__(self):
        return self.province

    class Meta:
        default_permissions = ()

class Cities(models.Model):
    cityid = models.CharField(max_length=20, unique=True, verbose_name=u'城市代码')
    city = models.CharField(max_length=50, verbose_name=u'城市')
    province = models.ForeignKey(Provinces, verbose_name=u'省份', related_name='province_city_set')

    def __unicode__(self):
        return self.city

    class Meta:
        default_permissions = ()

class Areas(models.Model):
    areaid = models.CharField(max_length=20, unique=True, verbose_name=u'区域代码')
    area = models.CharField(max_length=50, verbose_name=u'区县')
    city = models.ForeignKey(Cities, verbose_name=u'城市', related_name='city_area_set')

    def __unicode__(self):
        return self.area

    class Meta:
        default_permissions = ()
