#!/usr/bin/env python
# coding: utf8
'''
@Creator: valor7
@Email: valor7@163.com
@File: forms.py
@Time: 2017/10/15 16:05
@desc:
'''

from django import forms
from django.contrib.auth.models import Group

from models import *

class LoginForm(forms.Form):
    username = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control',
                                                                             'placeholder':'用户名', 'required':'required'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control',
                                                                 'placeholder':'密 码', 'required':'required'}))
    error_messages = {
        'invalid_login': ("Please enter a correct %(username)s and password. "
                           "Note that both fields may be case-sensitive."),
        'inactive': ("This account is inactive."),
    }

class UserForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('username', 'first_name', 'email', 'mobile', 'role', 'is_active')
        widgets = {
            'username': forms.TextInput(attrs={'class':'form-control', 'placeholder':'用户名', 'required':'required',
                                               'data-validate-length-range':'5,30'}),
            'first_name':forms.TextInput(attrs={'class':'form-control', 'required':'required'}),
            'email':forms.EmailInput(attrs={'class':'form-control', 'required':'required'}),
            'qq': forms.TextInput(attrs={'class': 'form-control', 'data-validate-length-range':'4,16'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control', 'data-validate-length':'11'}),
            'role': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'is_active':forms.CheckboxInput(attrs={'style':'padding-top:5px;'})
        }

class GroupForm(forms.ModelForm):
    #ModelForm生成下拉框
    def __init__(self,*args,**kwargs):
        super(GroupForm,self).__init__(*args,**kwargs)
        self.fields['command'].queryset = UserCommand.objects.filter(is_allow=True)
        self.fields['directory'].queryset = UserDirectory.objects.filter(is_allow=True)
    class Meta:
        model = UserGroup
        fields = ('group_name', 'command', 'directory', 'comment')
        widgets = {
            'group_name': forms.TextInput(attrs={'class':'form-control', 'required':'required', 'data-validate-length-range':'2,20'}),
            'command': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'directory': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control'})
        }

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ('deptname',)
        widgets = {
            'deptname': forms.TextInput(attrs={'class':'form-control', 'required':'required', 'data-validate-length-range':'2,20'}),
        }
