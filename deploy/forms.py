#!/usr/bin/env python
# coding: utf8
'''
@Creator: valor7
@Email: valor7@163.com
@File: forms.py
@Time: 2017/10/15 15:30
@desc:
'''

from django import forms
from .models import *

VISIBLE_CHOICES = (
        (0, u"私有"),
        (1, u"属组"),
        (2, u"公开"),
    )

class ModuleForm(forms.ModelForm):
    class Meta:
        model = ModuleUpload
        fields = ('name', 'module', 'upload_path', 'visible', 'remark')
        widgets = {
          'name': forms.TextInput(attrs={'class': 'form-control'}),
          'module': forms.TextInput(attrs={'class': 'form-control'}),
          'upload_path': forms.FileInput(),
          'visible': forms.RadioSelect(choices=VISIBLE_CHOICES, attrs={'class': 'flat'}),
          'remark': forms.TextInput(attrs={'class': 'form-control'})
        }

class SaltGroupForm(forms.ModelForm):
    class Meta:
        model = SaltGroup
        fields = ('nickname',)
        widgets = {
          'nickname': forms.TextInput(attrs={'class': 'form-control'}),
        }

class SaltFileForm(forms.Form):
    file_path = forms.FileField(label=u'选择文件',)
    remote_path = forms.CharField(label=u'远程路径',widget=forms.TextInput(attrs={'class': 'form-control'}))
    remark = forms.CharField(label=u'备注',widget=forms.TextInput(attrs={'class': 'form-control'}))

class ProjectForm(forms.ModelForm):
    # ModelForm生成下拉框
    def __init__(self, user, *args,**kwargs):
        super(ProjectForm,self).__init__(*args,**kwargs)
        if user.is_superuser:
            self.fields['user_group'].widget.choices = UserGroup.objects.values_list('pk', 'group_name')
            self.fields['salt_test'].widget.choices = [(0, '------')] + [(i.groupname, i.nickname) for i in
                                                                         SaltGroup.objects.all()]
            self.fields['salt_group'].widget.choices = [(0, '------')] + [(i.groupname, i.nickname) for i in
                                                                          SaltGroup.objects.all()]
        else:
            self.fields['user_group'].widget.choices = User.objects.get(pk=user.id).group.values_list('pk', 'group_name')
            self.fields['salt_test'].widget.choices = [(0, '------')] + [(i.groupname, i.nickname) for j in
                                                                         User.objects.get(pk=user.id).group.all() for i in
                                                                         j.group_usergroup_set.all()]
            self.fields['salt_group'].widget.choices = [(0, '------')] + [(i.groupname, i.nickname) for j in
                                                                         User.objects.get(pk=user.id).group.all() for i in
                                                                         j.group_usergroup_set.all()]

    def clean_src_passwd(self):
        instance = getattr(self, 'instance', None)
        if not self.cleaned_data['src_passwd']:
            return instance.src_passwd
        else:
            return self.cleaned_data['src_passwd']

    class Meta:
        model = Project
        fields = ('pname', 'src', 'src_user', 'src_passwd', 'path', 'process', 'user_group', 'salt_test', 'salt_group')
        widgets = {
            'pname': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'src': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'src_user': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'src_passwd': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': u'留空不更改密码'}),
            'path': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'/tmp/project', 'required': 'required'}),
            'process': forms.TextInput(attrs={'class': 'form-control',
                                              'placeholder': '/tmp/project start|/tmp/project reload|/tmp/project stop'}),
            'user_group': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'salt_test': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'salt_group': forms.Select(attrs={'class': 'form-control', 'required': 'required'})
        }

