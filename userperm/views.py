#!/usr/bin/env python
# coding: utf8
'''
@Creator: valor7
@Email: valor7@163.com
@File: views.py
@Time: 2017/10/15 16:10
@desc:
'''

from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404
from django.contrib.auth.decorators import login_required
from .models import *
from .forms import *

# Create your views here.

def UserIP(request):
    '''
    获取用户IP
    '''

    ip = ''
    if request.META.has_key('HTTP_X_FORWARDED_FOR'):
        ip = request.META['HTTP_X_FORWARDED_FOR']
    else:
        ip = request.META['REMOTE_ADDR']
    return ip

@login_required
def user_command_list(request):
    if request.user.is_superuser:
        command_list = UserCommand.objects.all()
        return render(request, 'userperm_command_list.html',
                      {'all_command': command_list})
    else:
        raise Http404

@login_required
def user_command_manage(request, id=None):
    if request.user.is_superuser:
        action = ''
        page_name = ''
        if id:
            command = get_object_or_404(UserCommand, pk=id)
            action = 'edit'
            page_name = '编辑命令'
        else:
            command = UserCommand()
            action = 'add'
            page_name = '新增命令'

        if request.method == 'GET':
            if request.GET.has_key('delete'):
                id = request.GET.get('id')
                command = get_object_or_404(UserCommand, pk=id)
                command.delete()

                Message.objects.create(type=u'权限控制', user=request.user.first_name, action=u'删除命令', action_ip=UserIP(request),content=u'删除命令 %s'%command.name)

                return redirect('command_list')

        if request.method == 'POST':
            form = CommandForm(request.POST, instance=command)
            if form.is_valid():
                if action == 'add':
                    command = form.save(commit=False)
                else:
                    form.save
                command.save()

                Message.objects.create(type=u'权限控制', user=request.user.first_name, action=page_name, action_ip=UserIP(request),content='%s %s'%(page_name,command.name))

                return redirect('command_list')

        else:
            form = CommandForm(instance=command)

        return render(request, 'userperm_command_manage.html', {
                      'form': form, 'action': action, 'page_name': page_name})
    else:
        raise Http404


@login_required
def user_dir_list(request):
    if request.user.is_superuser:
        dir_list = UserDirectory.objects.all()
        return render(request, 'userperm_directory_list.html',
                      {'all_dir': dir_list})
    else:
        raise Http404


@login_required
def user_dir_manage(request, id=None):
    if request.user.is_superuser:
        action = ''
        page_name = ''
        if id:
            directory = get_object_or_404(UserDirectory, pk=id)
            action = 'edit'
            page_name = '编辑目录'
        else:
            directory = UserDirectory()
            action = 'add'
            page_name = '新增目录'

        if request.method == 'GET':
            if request.GET.has_key('delete'):
                id = request.GET.get('id')
                directory = get_object_or_404(UserDirectory, pk=id)
                directory.delete()

                Message.objects.create(type=u'权限控制', user=request.user.first_name, action=u'删除目录', action_ip=UserIP(request),content=u'删除目录 %s'%directory.name)

                return redirect('dir_list')

        if request.method == 'POST':
            form = DirectoryForm(request.POST, instance=directory)
            if form.is_valid():
                if action == 'add':
                    directory = form.save(commit=False)
                else:
                    form.save
                directory.save()

                Message.objects.create(type=u'权限控制', user=request.user.first_name, action=page_name, action_ip=UserIP(request),content='%s %s'%(page_name,directory.name))

                return redirect('dir_list')

        else:
            form = DirectoryForm(instance=directory)

        return render(request, 'userperm_directory_manage.html', {
                      'form': form, 'action': action, 'page_name': page_name})
    else:
        raise Http404


@login_required
def audit_log(request):
    '''
    审计日志
    '''
    if request.user.is_superuser:
        logs = Message.objects.all()[:300]

        if request.method == 'GET':
            if request.GET.has_key('aid'):
                aid = request.get_full_path().split('=')[1]
                log_detail = Message.objects.filter(id=aid)
                return render(request, 'userperm_log_audit_detail.html',
                              {'log_detail': log_detail})

        return render(request, 'userperm_log_audit.html', {'all_logs': logs})
    else:
        raise Http404
