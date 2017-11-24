#!/usr/bin/env python
# coding: utf8
'''
@Creator: valor7
@Email: valor7@163.com
@File: views.py
@Time: 2017/10/15 15:28
@desc:
'''

from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404, HttpResponse

from django.http import StreamingHttpResponse

from django.contrib.auth.decorators import login_required
from django.db.models import Q

from deploy.saltapi import SaltAPI
from oms_valor7 import settings
from userperm.views import UserIP
from userperm.models import *
from .models import *
from .forms import *
# custom function
from tar_file import make_tar
from md5 import md5sum

try:
    import json
except ImportError:
    import simplejson as json

import time
import datetime
import shutil
import os
import re
import tarfile, zipfile
# Create your views here.

def dict_p(dict_a):
    r = ''
    iftrue = 0
    temp = []
    if isinstance(dict_a, dict):
        for k in dict_a.keys():
            if k == 'name':
                dict_a.pop(k)
                continue
            if k == 'result' and not k:
                temp.append(1)
            else:
                temp.append(0)
            v = dict_a[k]
            if isinstance(v,dict):
                dict_p(v)
            else:
                r = r + k + ': ' + str(v) + '<br />'
    if 1 in temp:
        iftrue = 1
    return {'result':r, 'iftrue':iftrue}

def list_dict(d):
    s = {}
    result = []
    for k,v in d.items():
        ret = {}
        for m,n in v.items():
            temp = dict_p(n)
            s[m] = temp['result']
            ret['iftrue'] = temp['iftrue']
        ret[k] = s
        result.append(ret)
    return result


def ProjectExec(sapi, tgt_list, fun, arg, expr_form):
    '''
    定义项目进程管理
    :param sapi:
    :param tgt_list:
    :param fun:
    :param arg:
    :param expr_form:
    :return:
    '''
    jid = sapi.remote_execution(tgt_list, fun, arg + ';echo ":::"$?', expr_form)
    s = SaltGroup.objects.get(groupname=tgt_list)
    s_len = s.minions.all().count()
    ret = ''
    rst = {}
    while (len(rst) < s_len):
        rst = sapi.salt_runner(jid)
        # time.sleep(1)
    for k in rst:
        ret = ret + u'主机：<span style="color:#e6db74">' + k + '</span><br />运行结果：<br />%s<br />' % rst[k]
        r = rst[k].split(':::')[-1].strip()
        if r != '0':
            ret = ret + '<span style="color:#f92672">%s</span> 执行失败！<br />' % arg + '<br />'
        else:
            ret = ret + '<span style="color:#e6db74">%s</span> 执行成功！<br />' % arg + '<br />'
    return {u'进程管理': {'result': ret}}

def RemoteExec(request, fun, group=False):
    '''
    定义远程命令函数
    '''
    command_list = [j.command.split(',') for i in request.user.group.all() for j in i.command.filter(is_allow=True)]
    command_list = [j for i in command_list for j in i]
    check = 2
    is_group = False
    ret = ''
    temp_dict = {}
    result = []
    jid = ''
    arg = ''
    if request.method == 'POST':
        if request.is_ajax():
            if request.POST.get('check_type') == 'panel-group':
                grp = request.POST.get('tgt_select')
                tgt_list = SaltGroup.objects.get(nickname=grp).groupname
                expr_form = 'nodegroup'
                is_group = True
            else:
                tgt_select = request.POST.getlist('tgt_select[]')
                if not tgt_select:
                    tgt_list = request.POST.get('tgt_select')
                else:
                    tgt_list = ','.join(tgt_select)
                expr_form = 'list'
            if fun == 'cmd.run':
                arg = request.POST.get('arg').strip(' ')
            else:
                arg = request.POST.get('arg')
                module = ModuleUpload.objects.get(pk=arg)
                if module.visible == 0:
                    arg = 'module.user_%s.%s'%(module.user.pk, module.module)
                elif module.visible == 2:
                    arg = 'module.public.%s'%module.module
                else:
                    arg = 'module.group_%s.%s'%(module.user_group.pk, module.module)
            if is_group:
                s = SaltGroup.objects.get(groupname=tgt_list)
                s_len = s.minions.all().count()
            else:
                s = tgt_list.split(',')
                s_len = len(s)

            sapi = SaltAPI(url=settings.SALT_API['url'],username=settings.SALT_API['user'],password=settings.SALT_API['password'])
            try:
                ## 远程命令
                if fun == 'cmd.run':
                    if arg in command_list and not request.user.is_superuser:
                        sret = {'CRITICAL': '不能执行此命令，老大会不高兴滴...', 'iftrue':2}
                        result.append(sret)
                    elif not arg or not tgt_list:
                        check = 1
                        sret = {'WARNING': '未选择主机或未输入命令...', 'iftrue':1}
                        result.append(sret)
                    else:
                        is_danger = []
                        for command in command_list:
                            for j in command.split(' '):
                                if j == arg:
                                    is_danger.append(1)
                        if is_danger and not request.user.is_superuser:
                            sret = {'CRITICAL': '不能执行此命令，老大会不高兴滴...', 'iftrue':2}
                            result.append(sret)
                        else:
                            jid = sapi.remote_execution(tgt_list, fun, arg + ';echo ":::"$?', expr_form)
                            rst = {}
                            t = 0
                            r = None
                            while (t < 5):
                                rst = sapi.salt_runner(jid)
                                if len(rst) == s_len:
                                    r = True
                                    break
                                t = t + 1
                                #time.sleep(1)
                            if r:
                                check = 0
                                for k, v in rst.items():
                                    check = v.split(':::')[-1].strip()
                                    result.append({k:v.replace('\n', '<br />'), 'iftrue':int(check)})
                            else:
                                check = 1
                                sret = {'INFO': '请稍候点击[重新查询]或到任务管理中查询结果<jid: %s>...'%jid, 'iftrue':1}
                                result.append(sret)
                ## 模块部署
                else:
                    jid = sapi.remote_execution(tgt_list, fun, arg, expr_form)
                    rst = {}
                    t = 0
                    r = None
                    while(t<3):
                        rst = sapi.salt_runner(jid)
                        if len(rst) == s_len:
                            r = True
                            break
                        t = t + 1
                        #time.sleep(1)
                    if r:
                        check = 0
                        sret = rst
                        result = list_dict(sret)
                    else:
                        check = 1
                        sret = {'INFO': {'消息': '请稍候点击[重新查询]或到任务管理中查询结果<jid: %s>...'%jid}, 'iftrue':1}
                        result.append(sret)
                    if not arg or not tgt_list:
                        check = 1
                        sret = {'WARNING': {'警告': '未选择主机或未输入命令...'}, 'iftrue':1}
                        result.append(sret)
                temp_dict['result'] = result
                temp_dict['jid'] = jid
            except:
                pass

    return {'result':result, 'sret':temp_dict, 'arg':arg, 'jid':jid, 'check':check, 'is_group':is_group}


def UploadFile(request, form, group=False):
    '''
    定义文件上传函数
    '''

    danger = []
    check = False
    is_group = False
    rst = ''
    ret = ''
    jid = ''
    fileupload = FileUpload()
    if request.method == 'POST':
        dir_list = [j.directory.split(',') for i in request.user.group.all() for j in i.directory.filter(is_allow=True)]
        dir_list = [j for i in dir_list for j in i]
        form = SaltFileForm(request.POST)
        if request.is_ajax():
            file_path = request.FILES.get('file_path', None)
            remote_path = request.POST.get('remote_path', None)
            remark = request.POST.get('remark', None)
            print file_path,'file',remote_path,'path',remark,'remark'*20
            if not file_path:
                return HttpResponse(json.dumps(u'未选择文件'))
            if remote_path not in dir_list or request.user.is_superuser:
                tag = '%s%s'%(request.user.id, datetime.datetime.now().strftime('%j%Y%m%d%H%M%S'))
                upload_dir = './media/salt/fileupload/user_%s/%s' % (request.user.id, tag)
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                dest = open(os.path.join(upload_dir, file_path.name), 'wb+')
                for chunk in file_path.chunks():
                    dest.write(chunk)
                dest.close()
                if request.POST.get('check_type') == 'panel-group':
                    grp = request.POST.get('tgt_select')
                    tgt_list = SaltGroup.objects.get(nickname=grp).groupname
                    expr_form = 'nodegroup'
                    is_group = True
                    tgt_select = [tgt_list]
                else:
                    tgt_select = request.POST.getlist('tgt_select')
                    tgt_list = ','.join(tgt_select)
                    expr_form = 'list'
                objs = [
                    FileUpload(
                        user = request.user,
                        target = tgt,
                        file_path = file_path,
                        remote_path = remote_path,
                        file_tag = tag,
                        remark = remark
                    )
                    for tgt in tgt_select
                    ]
                FileUpload.objects.bulk_create(objs)
                local_path = 'salt://fileupload/user_%s/%s/%s'%(request.user.id, tag, file_path.name)
                remote_path = '%s/%s'%(remote_path, file_path.name)
                sapi = SaltAPI(url=settings.SALT_API['url'],username=settings.SALT_API['user'],password=settings.SALT_API['password'])
                # 获取文件MD5
                file_md5 = md5sum(os.path.join(upload_dir, file_path.name))
                # 备份远程文件
                ret_bak = sapi.file_manage(tgt_list, 'file_bakup.Backup', remote_path, tag, file_md5, expr_form)
                # 上传文件到远程
                ret = sapi.file_copy(tgt_list, 'cp.get_file', local_path, remote_path, expr_form)
                # 分组上传文件时，只需从其中一台salt主机备份文件，备份完成后设置group_forloop为false
                group_forloop = True
                for k in ret:
                    if ret[k] and ret_bak[k] == 0:
                        rst = rst + u'主机：' + k + u'\n远程文件%s上传成功，备份成功...\n' % remote_path + '-' * 80 + '\n'
                        if request.POST.get('check_type') == 'panel-group' and group_forloop:
                            try:
                                FileRollback.objects.get_or_create(user=request.user,target=tgt_list,cur_path=remote_path,
                                                                   bak_path=remote_path,file_tag=tag,
                                                                   remark=remark,is_group=True)
                            except:
                                print 'not create'
                            group_forloop = False
                        else:
                            try:
                                FileRollback.objects.get_or_create(user=request.user,target=k,cur_path=remote_path,
                                                                   bak_path=remote_path,file_tag=tag,
                                                                   remark=remark)
                            except:
                                print 'not create'
                    elif ret[k] and ret_bak[k] == 1:
                            rst = rst + u'主机：' + k + u'\n远程文件%s未更改...\n' % remote_path + '-' * 80 + '\n'

                    elif ret[k] and not ret_bak[k]:
                            rst = rst + u'主机：' + k + u'\n远程文件%s上传成功，备份失败或不存在...\n' % remote_path + '-' * 80 + '\n'
                    else:
                        rst = rst + u'主机：' + k + u'\n远程文件%s上传失败...\n'%remote_path + '-'*80 + '\n'
        else:
            rst = u'无权限更改此目录'

    return {'ret':rst, 'check':check, 'is_group':is_group}

def AjaxResult(jid,result_type,check_type):
    '''
    定义ajax查询结果函数
    '''

    sret = {}
    sapi = SaltAPI(url=settings.SALT_API['url'],username=settings.SALT_API['user'],password=settings.SALT_API['password'])
    rtype = '远程命令'
    result = ''
    t = 0
    r = None
    while (t < 3):
        rst = sapi.salt_runner(jid)
        if rst:
            r = True
            break
        t = t + 1
        #time.sleep(1)

    if check_type == 'deploy':
        rtype = '模块部署'
        if r:
            sret = rst
            sret = list_dict(sret)
        else:
            sret = {'INFO': {'消息': '请稍候重新查询...'}}
        try:
            for k,v in sret.items():
                result = result + '主机：' + k + '<br /><p class="mydashed">结果：<br />'
                for m,n in v.items():
                    result = result + m + '<br />' + n
                result = result + "</p>"
        except:
            result = 'Err'
    else:
        if r:
            for k,v in rst.items():
                sret[k] = v.replace('\n', '<br />')
        else:
            sret = {'INFO': '请稍候重新查询...'}
        for k,v in sret.items():
            result = result + '主机：' + k + '<br /><p class="mydashed">结果：<br />' + v + '</p>'
    try:
        # 记录查询操作日志
        message = get_object_or_404(Message, action=jid)
        m = re.search('\[([^:]*)\]', message.content)
        arg = m.groups()[0]
        message.content = '%s：[%s]<br />原始输出：<br />%s'%(rtype, arg, result)
        message.audit_time = datetime.datetime.now()
        message.save()
    except:
        print 'Err'
        pass

    #if result_type == '1':
    return sret
    #else:
    #    return rst_all

@login_required
def salt_key_list(request):
    '''
    salt主机列表
    '''

    if request.user.is_superuser:
        minions = SaltHost.objects.filter(status=True)
        minions_pre = SaltHost.objects.filter(status=False)
        return render(request, 'salt_key_list.html', {'all_minions':minions,'all_minions_pre':minions_pre})
    else:
        raise Http404

@login_required
def salt_key_import(request):
    '''
    导入salt主机
    '''
    if request.user.is_superuser:
        sapi = SaltAPI(url=settings.SALT_API['url'],username=settings.SALT_API['user'],password=settings.SALT_API['password'])
        minions,minions_pre = sapi.list_all_key()
        alive = False
        ret_alive = sapi.salt_alive('*')
        for node_name in minions:
            try:
                alive = ret_alive[node_name]
                alive = True
            except:
                alive = False
            try:
                SaltHost.objects.create(hostname=node_name,alive=alive,status=True)
            except:
                salthost = SaltHost.objects.get(hostname=node_name)
                now = datetime.datetime.now()
                alive_old = SaltHost.objects.get(hostname=node_name).alive
                if alive != alive_old:
                    salthost.alive_time_last = now
                    salthost.alive = alive
                salthost.alive_time_now = now
                salthost.save()
        for node_name in minions_pre:
            try:
                SaltHost.objects.get_or_create(hostname=node_name,alive=alive,status=False)
            except:
                print 'not create'

        return redirect('key_list')
    else:
        raise Http404

@login_required
def salt_key_manage(request, hostname=None):
    '''
    接受或拒绝salt主机，同时更新数据库
    '''
    if request.user.is_superuser:
        if request.method == 'GET':
            sapi = SaltAPI(url=settings.SALT_API['url'],username=settings.SALT_API['user'],password=settings.SALT_API['password'])
            hostname = request.GET.get('hostname')
            salthost = SaltHost.objects.get(hostname=hostname)
            action = ''

            if request.GET.has_key('add'):
                ret = sapi.accept_key(hostname)
                if ret:
                    salthost.status=True
                    salthost.save()
                    result = 3
                    action = u'添加主机'
            if request.GET.has_key('delete'):
                ret = sapi.delete_key(hostname)
                if ret:
                    salthost.status=False
                    salthost.save()
                    result = 2
                    action = u'删除主机'
            if request.GET.has_key('flush') and request.is_ajax():
                # result: 0 在线 | 1 离线
                result = 0
                ret = sapi.salt_alive(hostname)
                try:
                    alive = ret[hostname]
                    alive = True
                except:
                    alive = False
                    result = 1
                salthost.alive=alive
                salthost.save()
                action = u'刷新主机'
                if action:
                    Message.objects.create(type=u'部署管理', user=request.user.first_name, action=action,
                                           action_ip=UserIP(request),
                                           content=u'%s %s' % (action, salthost.hostname))
                return HttpResponse(json.dumps(result))

            if action:
                    Message.objects.create(type=u'部署管理', user=request.user.first_name, action=action, action_ip=UserIP(request),content=u'%s %s'%(action,salthost.hostname))

        return redirect('key_list')
    else:
        raise Http404

@login_required
def salt_group_list(request):
    '''
    salt主机分组列表
    '''

    if request.user.is_superuser:
        groups = SaltGroup.objects.all()
        return render(request, 'salt_group_list.html', {'all_groups': groups})
    else:
        raise Http404

@login_required
def salt_group_manage(request, id=None):
    '''
    salt主机分组管理，同时更新salt-master配置文件
    '''
    if request.user.is_superuser:
        action = ''
        page_name = ''
        if id:
            group = get_object_or_404(SaltGroup, pk=id)
            action = 'edit'
            page_name = '编辑分组'
        else:
            group = SaltGroup()
            action = 'add'
            page_name = '新增分组'

        if request.method == 'GET':
            if request.GET.has_key('delete'):
                id = request.GET.get('id')
                group = get_object_or_404(SaltGroup, pk=id)
                group.delete()
                Message.objects.create(type=u'部署管理', user=request.user.first_name, action=u'删除分组', action_ip=UserIP(request),content='删除分组 %s'%group.nickname)
                with open('./saltconfig/nodegroup.conf','r') as f:
                    with open('./nodegroup', 'w') as g:
                        for line in f.readlines():
                            if group.groupname not in line:
                                g.write(line)
                shutil.move('./nodegroup','./saltconfig/nodegroup.conf')
                return redirect('group_list')

        if request.method == 'POST':
            form = SaltGroupForm(request.POST, instance=group)
            if form.is_valid():
                minion_select = request.POST.getlist('minion_sel')
                minion_delete = request.POST.getlist('minion_del')
                # 前台分组以别名显示，组名不变
                if action == 'add':
                    group = form.save(commit=False)
                    group.groupname = form.cleaned_data['nickname']
                elif action == 'edit':
                    form.save()
                group.save()
                group.minions.add(*minion_select)
                group.minions.remove(*minion_delete)
                group.save()
                Message.objects.create(type=u'部署管理', user=request.user.first_name, action=page_name, action_ip=UserIP(request),content='%s %s'%(page_name,group.nickname))

                minions_l = []
                for m in group.minions.values('hostname'):
                    minions_l.append(m['hostname'])
                minions_str = ','.join(minions_l)
                try:
                    with open('./saltconfig/nodegroup.conf','r') as f:
                        with open('./nodegroup', 'w') as g:
                            for line in f.readlines():
                                if group.groupname not in line:
                                    g.write(line)
                            g.write("  %s: 'L@%s'\n"%(group.groupname,minions_str))
                    shutil.move('./nodegroup','./saltconfig/nodegroup.conf')
                except:
                    with open('./saltconfig/nodegroup.conf', 'w') as g:
                        g.write("nodegroups:\n  %s: 'L@%s'\n"%(group.groupname,minions_str))

                import subprocess
                subprocess.Popen('systemctl restart salt-master salt-api', shell=True)
                return redirect('group_list')
        else:
            form = SaltGroupForm(instance=group)

        return render(request, 'salt_group_manage.html', {'form':form, 'action':action, 'page_name':page_name, 'aid':id})
    else:
        raise Http404

@login_required
def salt_module_list(request):
    '''
    模块列表
    '''
    if request.user.has_perm('deploy.view_deploy'):
        if request.user.is_superuser:
            module_list = ModuleUpload.objects.all()
        else:
            # 获取用户创建或公开模块
            module_visible_list = [{'pk': i.pk, 'name': i.name, 'module': i.module, 'remark': i.remark, 'user': i.user}
                                   for i in ModuleUpload.objects.filter(Q(user=request.user) | Q(visible=2))]
            # 获取用户组模块
            module_user_group_list = [{'pk': i.pk, 'name': i.name, 'module': i.module, 'remark': i.remark, 'user': i.user}
                                      for g in User.objects.get(pk=request.user.pk).group.all() for i in ModuleUpload.objects.filter(user_group=g)]
            # 合并list
            module_list = module_visible_list + [i for i in module_user_group_list if i not in module_visible_list]
        return render(request, 'salt_module_list.html', {'modules':module_list})
    else:
        raise Http404

@login_required
def salt_module_manage(request, id=None):
    '''
    模块管理
    '''
    if request.user.has_perms(['deploy.view_deploy', 'deploy.edit_module']):
        ret = ''
        upload_stat = True
        if id:
            module = get_object_or_404(ModuleUpload, pk=id)
            if request.user.pk != module.user.pk and not request.user.is_superuser:
                return HttpResponse("Not Allowed!")
            old_path = module.upload_path.path.split('.')
            action = 'edit'
            page_name = '编辑模块'
        else:
            module = ModuleUpload()
            action = 'add'
            page_name = '新增模块'

        if request.method == 'GET':
            if request.GET.has_key('delete'):
                id = request.GET.get('id')
                module = get_object_or_404(ModuleUpload, pk=id)
                if request.user.pk != module.user.pk and not request.user.is_superuser:
                    return HttpResponse("Not Allowed!")
                module.delete()
                Message.objects.create(type=u'部署管理', user=request.user.first_name, action=u'删除模块', action_ip=UserIP(request),content=u'删除模块 %s'%module.name)
                cur_path = module.upload_path.path.split('.')[0]
                try:
                    os.remove('%s.sls'%(cur_path))
                except:
                    shutil.rmtree(cur_path, ignore_errors=True)
                return redirect('module_list')

        if request.method == 'POST':
            form = ModuleForm(request.POST, request.FILES, instance=module)
            if form.is_valid():
                visible = form.cleaned_data['visible']
                module_list = form.cleaned_data['module'].split('.')
                user_group = request.POST.get('user_group')

                if visible == 0:
                    ext_path = './media/salt/module/user_%s' % request.user.id
                    salt_path = 'salt://module/user_%s/%s' % (request.user.id, module_list[0])
                elif visible == 2:
                    ext_path = './media/salt/module/public'
                    salt_path = 'salt://module/public/%s'%module_list[0]
                else:
                    ext_path = './media/salt/module/group_%s' % user_group
                    salt_path = 'salt://module/group_%s/%s' % (user_group, module_list[0])
                file_exists = request.POST.get('upload_path')
                file_name = form.cleaned_data['upload_path']
                file_ext = str(file_name).split('.')[-1]
                ext = ['bz2','gz','zip','sls']
                if file_ext in ext:
                    if action == 'add':
                        module = form.save(commit=False)
                        module.user = request.user
                    else:
                        form.save
                    if user_group:
                        module.user_group = UserGroup.objects.get(pk=user_group)
                    module.save()

                    Message.objects.create(type=u'部署管理', user=request.user.first_name, action=page_name, action_ip=UserIP(request),content='%s %s'%(page_name,module.name))

                    src = module.upload_path.path

                    if file_exists == None:
                        try:
                            os.remove('%s.sls'%old_path[0])
                        except:
                            pass
                        try:
                            if file_ext == 'zip':
                                tar = zipfile.ZipFile(src)
                            else:
                                tar = tarfile.open(src)

                            tar.extractall(path=ext_path)
                            tar.close()
                            with open('%s/%s/%s.sls'%(ext_path,module_list[0],module_list[1]), 'r+') as f:
                                t = f.read()
                                t = t.replace('SALTSRC', salt_path)
                                f.seek(0, 0)
                                f.write(t)
                            ret = u'模块 %s 已上传完成！'%(file_name)
                        except:
                            upload_stat = False
                            ret = u'模块 %s 上传失败，请上传.sls文件或.tar.gz/.tar.bz2/.zip压缩包并确认压缩文件是否损坏！'%(file_name)
                        try:
                            os.remove(src)
                        except:
                            shutil.rmtree(src, ignore_errors=True)
                            pass

                    if upload_stat:
                        return redirect('module_list')
                    else:
                        return render(request, 'salt_module_manage.html', {'form':form, 'action':action, 'page_name':page_name, 'ret':ret})
                else:
                    ret = u'不支持的文件格式，请上传.sls文件或.tar.gz/.tar.bz2/.zip压缩包！'
        else:
            form = ModuleForm(instance=module)
        return render(request, 'salt_module_manage.html', {'form':form, 'action':action, 'page_name':page_name, 'ret':ret, 'id':id})
    else:
        raise Http404

@login_required
def salt_ajax_minions(request):
    '''
    获取不同分组下的主机列表
    '''
    if request.user.has_perms(['deploy.view_deploy']):
        ret = []
        if request.method == 'POST':
            grp = request.POST.get('tgt_select', None)
            tgt_select = SaltGroup.objects.get(nickname=grp).groupname
            if request.is_ajax():
                group = SaltGroup.objects.get(groupname=tgt_select)
                group_minions = group.minions.all()
                for i in group_minions:
                    ret.append(i.hostname)

                return HttpResponse(json.dumps(ret))
    else:
        raise Http404

@login_required
def salt_ajax_result(request):
    '''
    ajax方式查询结果
    '''
    if request.user.has_perm('deploy.edit_deploy'):
        if request.method == 'POST':
            check_type = request.POST.get('type', None)
            jid = request.POST.get('jid', None)
            result_type = request.POST.get('result_type', None)
            if request.is_ajax():
                rst_all = AjaxResult(jid,result_type,check_type)

                return HttpResponse(json.dumps(rst_all))
    else:
        raise Http404

@login_required
def salt_remote_exec(request):
    '''
    salt远程命令界面
    '''
    if request.user.has_perm('deploy.view_deploy'):
        return render(request, 'salt_remote_exec.html', {'groups':['panel-single','panel-group']})
    else:
        raise Http404

@login_required
def salt_ajax_remote_exec(request):
    '''
    salt远程命令执行
    '''
    if request.user.has_perms(['deploy.view_deploy', 'deploy.edit_deploy']):
        result = ''
        rst = RemoteExec(request, fun='cmd.run')
        if not rst['jid']:
            rst['jid'] = 'DANGER'
        try:
            for i in rst['sret']['result']:
                for k, v in i.items():
                    if k != 'iftrue':
                        result = result + '主机：' + k + '<br /><p class="mydashed">结果：<br />' + v + '<br />'
                result = result + 'retcode: %s</p>' % i['iftrue']
        except:
            result = 'Err'

        Message.objects.create(type=u'部署管理', user=request.user.first_name, action=rst['jid'], action_ip=UserIP(request),
                               content=u'远程命令 [%s]<br />原始输出：<br />%s' % (rst['arg'], result))
        return HttpResponse(json.dumps(rst['sret']))
    else:
        raise Http404

@login_required
def salt_module_deploy(request):
    '''
    salt模块部署界面
    '''
    if request.user.has_perm('deploy.view_deploy'):
        modules = ModuleUpload.objects.all()
        return render(request, 'salt_module_deploy.html', {'modules':modules, 'groups':['panel-single','panel-group']})
    else:
        raise Http404

@login_required
def salt_ajax_module_deploy(request):
    '''
    salt模块部署
    '''
    if request.user.has_perms(['deploy.view_deploy', 'deploy.edit_deploy']):
        result = ''
        rst = RemoteExec(request, fun='state.sls')
        try:
            for i in rst['sret']['result']:
                for k, v in i.items():
                    if k != 'iftrue':
                        result = result + '主机：' + k + '<br /><p class="mydashed">结果：<br />'
                        for m, n in v.items():
                            result = result + m + '<br />' + n
                result = result + 'retcode: %s</p>' % i['iftrue']
        except:
            result = 'Err'

        Message.objects.create(type=u'部署管理', user=request.user.first_name, action=rst['jid'], action_ip=UserIP(request),
                               content=u'模块部署 [%s]<br />原始输出：<br />%s' % (rst['arg'], result))
        return HttpResponse(json.dumps(rst['sret']))
    else:
        raise Http404

@login_required
def salt_advanced_manage(request):
    if request.user.has_perms(['deploy.view_deploy']):
        ret = ''
        sret = {}
        result = []
        check = 2
        is_group = False
        if request.method == 'POST':
            if request.user.has_perms(['deploy.view_deploy', 'deploy.edit_deploy']):
                if request.is_ajax():
                    tgt_selects = request.POST.getlist('tgt_select', None)
                    args = request.POST.getlist('arg', None)
                    checkgrp = request.POST.getlist('ifcheck', None)
                    check_type = request.POST.get('check_type', None)
                    if check_type == 'panel-group':
                        is_group = True
                        expr_form = 'nodegroup'
                    else:
                        expr_form = 'list'
                    s='::'.join(str(i) for i in checkgrp)
                    checkgrp = s.replace('0::1','1').split('::')
                    sapi = SaltAPI(url=settings.SALT_API['url'],username=settings.SALT_API['user'],password=settings.SALT_API['password'])
                    for i in range(0,len(tgt_selects)):
                        tgt = tgt_selects[i]
                        try:
                            jid = sapi.remote_execution(tgt, 'cmd.run', args[i] + ';echo ":::"$?', expr_form)
                            if is_group:
                                ## 获取组内主机数量
                                s = SaltGroup.objects.get(groupname=tgt)
                                s_len = s.minions.all().count()
                            else:
                                s_len = 1
                            rst = {}
                            t = 0
                            r = None
                            while (t < 5):
                                rst = sapi.salt_runner(jid)
                                if len(rst) == s_len:
                                    r = True
                                    break
                                t = t + 1
                                #time.sleep(1)
                            if r:
                                sret = {}
                                j = 0
                                for k, v in rst.items():
                                    iftrue = v.split(':::')[-1].strip()
                                    if iftrue != '0':
                                        check = 2
                                        if checkgrp[i] == '0':
                                            try:
                                                Message.objects.create(type=u'部署管理', user=request.user.first_name,
                                                                       action=jid, action_ip=UserIP(request),
                                                                       content=u'高级管理 Test')
                                            except:
                                                print 'Log Err'
                                            return HttpResponse(json.dumps(ret))
                                        else:
                                            continue
                                    else:
                                        check = 0
                                    if is_group:
                                        sret['L%s-%s: %s'%(i,j,k)] = v.replace('\n', '<br />')
                                    else:
                                        sret['L%s: %s' % (i, k)] = v.replace('\n', '<br />')
                                    sret['iftrue'] = check
                                    j = j + 1
                            else:
                                check = 1
                                sret = {'INFO': '请稍候点击[重新查询]或到任务管理中查询结果<jid: %s>...'%jid}

                            result.append(sret)
                        except:
                            print 'Err'
                    try:
                        Message.objects.create(type=u'部署管理', user=request.user.first_name, action=jid, action_ip=UserIP(request),content=u'高级管理 Test')
                    except:
                        print 'Log Err'

                    return HttpResponse(json.dumps(result))
            else:
                raise Http404

        return render(request, 'salt_remote_exec_advance.html', {})
    else:
        raise Http404

@login_required
def salt_file_upload(request):
    '''
    文件上传界面
    '''
    if request.user.has_perm('deploy.view_filemanage'):
        form = SaltFileForm()
        return render(request, 'salt_file_upload.html', {'form':form,'groups':['panel-single','panel-group']})
    else:
        raise Http404

@login_required
def salt_file_download(request):
    def file_iterator(file_name, chunk_size=512):
        with open(file_name) as f:
            while True:
                c = f.read(chunk_size)
                if c:
                    yield c
                else:
                    break

    if request.user.has_perms(['deploy.view_filemanage']):
        sapi = SaltAPI(url=settings.SALT_API['url'],username=settings.SALT_API['user'],password=settings.SALT_API['password'])
        if request.method == 'POST':
            if request.user.has_perms(['deploy.view_filemanage', 'deploy.edit_filedownload']):
                if request.POST.get('type') == 'list':
                    rst = RemoteExec(request, fun='cmd.run')
                    return HttpResponse(json.dumps(rst['ret']))
                else:
                    tgt_list = request.POST.get('tgt_select', None)
                    arg = request.POST.get('arg', None)
                    jid = sapi.remote_execution(tgt_list, 'cmd.run', 'if [ -d %s ];then echo 0;else echo 1;fi'%arg, 'list')
                    rst = sapi.salt_runner(jid)
                    if rst[tgt_list] == '0':
                        return HttpResponse(json.dumps(arg))
                    elif rst[tgt_list] == '1':
                        return HttpResponse(json.dumps("download"))
                    else:
                        print 'Err'
            else:
                raise Http404
        if request.method == 'GET':
            if request.user.has_perms(['deploy.view_filemanage', 'deploy.edit_filedownload']):
                if request.GET.get('type') == 'download':
                    tgt_select = request.GET.get('tgt_select', None)
                    arg = request.GET.get('arg', None)
                    remote_file = arg
                    ret_bak = sapi.file_bak(tgt_select, 'cp.push', remote_file, 'list')
                    if tgt_select == 'localhost':
                        return render(request,'redirect.html',{})
                    remote_path = remote_file.replace(remote_file.split('/')[-1],'')
                    dl_path = './media/salt/filedownload/user_%s/%s%s'%(request.user.id,tgt_select,remote_path)
                    dl_file = '%s%s'%(dl_path,remote_file.split('/')[-1])
                    if not os.path.exists(dl_path):
                        os.makedirs(dl_path)
                    try:
                        shutil.copy('/var/cache/salt/master/minions/%s/files/%s' % (tgt_select,remote_file), dl_file)
                        tar_file = make_tar(dl_file,'/tmp')
                        dl_filename = 'attachment;filename="{0}"'.format(tar_file.replace('/tmp/','%s%s'%(tgt_select,remote_path)))
                        ret = u'主机：%s\n结果：远程文件 %s 下载成功！'%(tgt_select,remote_file)
                        Message.objects.create(type=u'文件管理', user=request.user.first_name, action=u'文件下载', action_ip=UserIP(request),content=u'下载文件 \n%s'%ret)
                        response = StreamingHttpResponse(file_iterator(tar_file))
                        response['Content-Type'] = 'application/octet-stream'
                        response['Content-Disposition'] = dl_filename

                        return response

                    except:
                        print 'No such file or dirctory'
                        ret = u'主机：%s\n结果：远程文件 %s 下载失败，请确认文件是否存在！'%(tgt_select,remote_file)
                        Message.objects.create(type=u'文件管理', user=request.user.first_name, action=u'文件下载', action_ip=UserIP(request),content=u'下载文件 \n%s'%ret)
                        return render(request, 'salt_file_download.html', {'ret':ret})
            else:
                raise Http404
        return render(request, 'salt_file_download.html', {})
    else:
        raise Http404

@login_required
def salt_ajax_file_upload(request):
    '''
    执行文件上传
    '''
    if request.user.has_perms(['deploy.view_filemanage', 'deploy.edit_fileupload']):
        form = SaltFileForm()
        ret = UploadFile(request,form=form)
        Message.objects.create(type=u'文件管理', user=request.user.first_name, action=u'文件上传', action_ip=UserIP(request),content=u'上传文件 %s'%ret['ret'])
        return HttpResponse(json.dumps(ret['ret']))
    else:
        raise Http404

@login_required
def salt_file_rollback(request):
    '''
    文件回滚界面
    '''
    if request.user.has_perm('deploy.view_filemanage'):
        form = SaltFileForm()
        return render(request, 'salt_file_rollback.html', {'form':form,'groups':['panel-single','panel-group']})
    else:
        raise Http404

@login_required
def salt_ajax_file_rollback(request):
    '''
    执行文件回滚
    '''
    if request.user.has_perms(['deploy.view_filemanage', 'deploy.edit_fileupload']):
        true = True
        if request.method == 'POST':
            if request.is_ajax():
                r_list = []
                if request.POST.get('check_type') == 'rollback_file':
                    if request.POST.get('get_type') == 'panel-group':
                        grp = request.POST.get('tgt_select')
                        tgt_select = SaltGroup.objects.get(nickname=grp).groupname
                    else:
                        tgt_select = request.POST.get('tgt_select')
                    rollback_list = FileRollback.objects.filter(target=tgt_select)
                    r_list = []
                    for r in rollback_list:
                        r_list.append(r.cur_path)
                    func = lambda x,y:x if y in x else x + [y]
                    r_list = reduce(func,[[],]+r_list)
                    return HttpResponse(json.dumps(r_list))

                if request.POST.get('check_type') == 'rollback_history_list':
                    if request.POST.get('get_type') == 'panel-group':
                        grp = request.POST.get('tgt_select')
                        tgt_select = SaltGroup.objects.get(nickname=grp).groupname
                    else:
                        tgt_select = request.POST.get('tgt_select')
                    cur_path = request.POST.get('rollback_list', None)
                    rollback_history_list = FileRollback.objects.filter(cur_path=cur_path).filter(target=tgt_select)
                    for r in rollback_history_list:
                        r_list.append(r.file_tag)
                    return HttpResponse(json.dumps(r_list))

                if request.POST.get('check_type') == 'rollback_history_remark':
                    if request.POST.get('get_type') == 'panel-group':
                        grp = request.POST.get('tgt_select')
                        tgt_select = SaltGroup.objects.get(nickname=grp).groupname
                    else:
                        tgt_select = request.POST.get('tgt_select')
                    cur_path = request.POST.get('rollback_list', None)
                    file_tag = request.POST.get('rollback_remark', None)
                    rollback_history_remark = FileRollback.objects.filter(cur_path=cur_path).filter(file_tag=file_tag)\
                        .filter(target=tgt_select)
                    for r in rollback_history_remark:
                        r_list.append(r.remark)

                    return HttpResponse(json.dumps(r_list))

                else:
                    if request.POST.get('check_type') == 'panel-group':
                        grp = request.POST.get('tgt_select')
                        tgt_select = SaltGroup.objects.get(nickname=grp).groupname
                        expr_form = 'nodegroup'
                    else:
                        tgt_select = request.POST.get('tgt_select')
                        expr_form = 'list'
                    remote_path = request.POST.get('remote_path')
                    file_tag = request.POST.get('tag')
                    sapi = SaltAPI(url=settings.SALT_API['url'],username=settings.SALT_API['user'],password=settings.SALT_API['password'])
                    file_tag_new = '%s%s' % (request.user.id, datetime.datetime.now().strftime('%j%Y%m%d%H%M%S'))
                    # 回滚前备份远程文件
                    ret_bak = sapi.file_manage(tgt_select, 'file_bakup.Backup', remote_path, file_tag_new, None, expr_form)
                    # 文件回滚
                    ret = sapi.file_manage(tgt_select, 'file_bakup.Rollback', remote_path, file_tag, None, expr_form)
                    rst = ''
                    for k in ret:
                        rst = rst + u'主机：' + k + '\n回滚结果：\n' + ret[k] + '\n' + '-'*80 + '\n'

                    Message.objects.create(type=u'文件管理', user=request.user.first_name, action=u'文件回滚', action_ip=UserIP(request),content=u'文件回滚 %s'%rst)

                    return HttpResponse(json.dumps(rst))
    else:
        raise Http404

@login_required
def salt_task_list(request):
    '''
    任务列表
    '''
    if request.user.has_perm('userperm.view_message'):
        if request.method == 'GET':
            if request.GET.has_key('tid'):
                tid = request.get_full_path().split('=')[1]
                log_detail = Message.objects.filter(user=request.user.first_name).filter(id=tid).exclude(type=u'用户登录').exclude(type=u'用户退出')
                return render(request, 'salt_task_detail.html', {'log_detail':log_detail})

        logs = Message.objects.filter(user=request.user.first_name).exclude(type=u'用户登录').exclude(type=u'用户退出')[:200]

        return render(request, 'salt_task_list.html', {'all_logs':logs})
    else:
        raise Http404

@login_required
def salt_task_check(request):
    '''
    任务查询
    '''
    return render(request, 'salt_task_check.html', {})

@login_required
def salt_task_running(request):
    '''
    获取运行中的任务
    '''
    ret = []
    if request.method == 'POST':
        if request.user.has_perms(['userperm.view_message', 'deploy.edit_deploy']):
            if request.is_ajax():
                sapi = SaltAPI(url=settings.SALT_API['url'],username=settings.SALT_API['user'],password=settings.SALT_API['password'])
                rst = sapi.salt_running_jobs()
                for k,v in rst.items():
                    dict={}
                    dict['jid'] = k
                    dict['func'] = v['Function']
                    dict['tgt_type'] = v['Target-type']
                    dict['running'] = v['Arguments'][0].replace(';echo ":::"$?','')
                    str_tgt = ''
                    for i in v['Running']:
                        for m,n in i.items():
                            str_tgt = str_tgt + m + ':' + str(n) + '<br />'
                    dict['tgt_pid'] = str_tgt
                    ret.append(dict)
                return HttpResponse(json.dumps(ret))
    if request.GET.has_key('delete'):
        jid = request.GET.get('jid')
        import subprocess
        p=subprocess.Popen("salt '*' saltutil.term_job %s"%jid, shell=True, stdout=subprocess.PIPE)
        out=p.stdout.readlines()
        return HttpResponse(json.dumps('Job %s killed.'%jid))

    return render(request, 'salt_task_running_list.html', {})

@login_required
def project_list(request):
    '''
    项目列表
    '''
    if request.user.has_perm('deploy.view_project'):
        if request.user.is_superuser:
            project_list = Project.objects.all()
        else:
            user_group = User.objects.get(pk=request.user.id).group.all()
            for g in user_group:
                project_list = Project.objects.filter(user_group=g)
        return render(request, 'salt_project_list.html', {'projects':project_list})
    else:
        raise Http404

@login_required
def project_manage(request, id=None):
    '''
    项目管理
    :param request:
    :param id:
    :return:
    '''
    rsync_conf = './media/salt/rsync'
    if request.user.has_perm('deploy.view_project'):
        content = ''
        if id:
            project = get_object_or_404(Project, pk=id)
            action = 'edit'
            page_name = '编辑项目'
            try:
                with open('%s/%s.list' % (rsync_conf, project.name), 'r') as f:
                    content = f.read()
            except:
                pass
        else:
            project = Project()
            action = 'add'
            page_name = '新增项目'

        if request.method == 'GET':
            if request.GET.has_key('delete'):
                id = request.GET.get('id')
                project = get_object_or_404(Project, pk=id)
                project.delete()
                Message.objects.create(type=u'部署管理', user=request.user.first_name, action=u'删除项目',
                                       action_ip=UserIP(request), content=u'删除项目 %s' % project.pname)
                return redirect('project_list')

        if request.method == 'POST':
            form = ProjectForm(request.user, request.POST, instance=project)
            if form.is_valid():
                if action == 'add':
                    project = form.save(commit=False)
                    project.user = request.user
                else:
                    form.save
                project.name = form.cleaned_data['src'].split('/')[-1].replace('.git', '')
                project.save()
                exclude = request.POST.get('exclude')
                try:
                    if not os.path.isdir(rsync_conf):
                        os.makedirs(rsync_conf)
                    with open('%s/%s.list'%(rsync_conf,project.name),'w') as f:
                        f.write(exclude)
                except:
                    pass
                Message.objects.create(type=u'部署管理', user=request.user.first_name, action=page_name,
                                       action_ip=UserIP(request), content='%s %s' % (page_name, project.pname))

                return redirect('project_list')
        else:
            form = ProjectForm(request.user, instance=project)

        return render(request, 'salt_project_manage.html', {'form':form, 'action':action, 'page_name':page_name, 'aid':id, 'content':content})
    else:
        raise Http404

@login_required
def project_deploy(request):
    '''
    项目部署
    :param request:
    :return:
    '''
    if request.user.has_perm('deploy.edit_project'):
        if request.method == 'GET':
            if request.is_ajax():
                id = request.GET.get('id')
                env = request.GET.get('env')
                project = Project.objects.get(pk=id)
                if env == '0':
                    tgt_list = project.salt_test
                elif env == '1':
                    tgt_list = project.salt_group
                else:
                    pass
                if tgt_list == '0':
                    ret = {u'发布异常':{'result':u'请确认是否配置测试/正式环境'}}
                    if request.GET.has_key('get_rollback'):
                        ret = {'-1': u'请确认是否配置测试/正式环境'}
                    return HttpResponse(json.dumps(ret))
                expr_form = 'nodegroup'
                action = ''
                url = project.src.split('//')
                sapi = SaltAPI(url=settings.SALT_API['url'], username=settings.SALT_API['user'],
                               password=settings.SALT_API['password'])
                dtime = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                ret = sapi.file_copy(tgt_list, 'cp.get_file', 'salt://rsync/%s.list' % project.name,
                                       '/srv/salt/%s.list' % project.name, 'nodegroup')
                if request.GET.has_key('init'):
                    action = u'初始化项目'
                    ret = sapi.project_manage(tgt_list, 'project_manage.ProjectSync', project.name,
                                              '%s//%s:%s@%s' % (url[0], project.src_user, project.src_passwd, url[1]),
                                              project.path, 'init', dtime, expr_form)

                if request.GET.has_key('update'):
                    action = u'更新项目'
                    try:
                        ret = sapi.project_manage(tgt_list, 'project_manage.ProjectSync', project.name,
                                              '%s//%s:%s@%s' % (url[0], project.src_user, project.src_passwd, url[1]),
                                              project.path, 'update', dtime, expr_form)
                        for _, v in ret.items():
                            if v['tag']:
                                ProjectRollback.objects.create(name=project, tag=v['tag'], env=env)
                                break
                    except:
                        ret = {u'更新异常':{'result':u'更新失败，检查项目是否发布'}}

                if request.GET.has_key('get_rollback'):
                    action = u'获取备份'
                    ret = {i['pk']: i['tag'] for i in
                           ProjectRollback.objects.filter(name=id).filter(env=env).values('pk', 'tag')}
                    if not ret:
                        ret = {'0':'No backup found.'}

                if request.GET.has_key('rollback_delete'):
                    action = u'删除备份'
                    tag = request.GET.get('tag')
                    enforce = request.GET.get('enforce')
                    ret = sapi.project_manage(tgt_list, 'project_manage.ProjectClean', project.name, tag,
                                              project.path, 'delete', dtime, expr_form)
                    for _, v in ret.items():
                        if v['tag'] or enforce == '1':
                            ProjectRollback.objects.get(name=project, tag=tag, env=env).delete()
                            break

                if request.GET.has_key('rollback'):
                    action = u'回滚项目'
                    tag = request.GET.get('tag')
                    ret = sapi.project_manage(tgt_list, 'project_manage.ProjectRollback', project.name, tag,
                                              project.path, 'rollback', dtime, expr_form)

                if request.GET.has_key('start'):
                    action = u'启动进程'
                    tag = request.GET.get('tag')
                    if tag:
                        ret = ProjectExec(sapi, tgt_list, 'cmd.run', tag, expr_form)
                    else:
                        ret = {u'进程管理': {'result': u'未配置启动项'}}

                if request.GET.has_key('reload'):
                    action = u'重启进程'
                    tag = request.GET.get('tag')
                    if tag:
                        ret = ProjectExec(sapi, tgt_list, 'cmd.run', tag, expr_form)
                    else:
                        ret = {u'进程管理': {'result': u'未配置重启项'}}

                if request.GET.has_key('stop'):
                    action = u'停止进程'
                    tag = request.GET.get('tag')
                    if tag:
                        ret = ProjectExec(sapi, tgt_list, 'cmd.run', tag, expr_form)
                    else:
                        ret = {u'进程管理': {'result': u'未配置停止项'}}

                Message.objects.create(type=u'项目管理', user=request.user.first_name, action=action,
                                       action_ip=UserIP(request), content='%s %s' % (project.pname, ret))

                return HttpResponse(json.dumps(ret))

        return redirect(project_list)
    else:
        raise Http404
