#!/usr/bin/env python
# coding: utf8
'''
@Creator: valor7
@Email: valor7@163.com
@File: views.py
@Time: 2017/10/15 15:34
@desc:
'''

from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404, HttpResponse
from django.contrib.auth.decorators import login_required

from asset_info import MultipleCollect
from models import ServerAsset, IdcAsset
from deploy.models import SaltHost
from geo import GeoInput
from asset.forms import IdcAssetForm

import StringIO
import xlwt
import json

# Create your views here.
def SheetWrite(sheet, row, serverasset, style):
    sheet.write(row,0, serverasset.hostname+'['+serverasset.nodename+']', style)
    sheet.write(row,1, serverasset.os, style)
    sheet.write(row,2, serverasset.kernel, style)
    sheet.write(row,3, serverasset.saltversion, style)
    sheet.write(row,4, serverasset.zmqversion, style)
    sheet.write(row,5, serverasset.shell, style)
    sheet.write(row,6, serverasset.locale, style)
    sheet.write(row,7, serverasset.selinux, style)
    sheet.write(row,8, serverasset.cpu_model, style)
    sheet.write(row,9, serverasset.cpu_nums, style)
    sheet.write(row,10, serverasset.memory, style)
    sheet.write(row,11, serverasset.disk, style)
    sheet.write(row,12, serverasset.network, style)
    sheet.write(row,13, serverasset.virtual, style)
    sheet.write(row,14, serverasset.sn, style)
    sheet.write(row,15, serverasset.manufacturer+' '+serverasset.productname, style)
    sheet.write(row,16, serverasset.idc, style)

@login_required
def get_server_asset_info(request):
    '''
    获取服务器资产信息
    '''
    idc = [i['idc_name'] for i in IdcAsset.objects.values('idc_name')]
    if request.method == 'GET':
        if request.user.has_perm('asset.view_asset'):
            ret = ''
            all_server = ServerAsset.objects.all()
            if request.GET.has_key('aid'):
                aid = request.get_full_path().split('=')[1]
                server_detail = ServerAsset.objects.filter(id=aid)
                return render(request, 'asset_server_detail.html', {'server_detail': server_detail})

            if request.GET.has_key('get_idc'):
                return HttpResponse(json.dumps(idc))

            if request.GET.has_key('action'):
                if request.user.has_perm('asset.edit_asset'):
                    action = request.get_full_path().split('=')[1]
                    if action == 'flush':
                        q = SaltHost.objects.filter(alive=True)
                        tgt_list = []
                        [tgt_list.append(i.hostname) for i in q]
                        ret = MultipleCollect(tgt_list)
                        for i in ret:
                            try:
                                server_asset = get_object_or_404(ServerAsset, nodename=i['nodename'])
                                for j in i:
                                    if i[j] != 'Nan':
                                        setattr(server_asset, j, i[j])
                                server_asset.save()
                            except:
                                server_asset = ServerAsset()
                                for j in i:
                                    setattr(server_asset, j, i[j])
                                server_asset.save()
                        return redirect('server_info')
                else:
                    raise Http404
            if request.GET.has_key('export'):
                response = HttpResponse(content_type='application/vnd.ms-excel')
                response['Content-Disposition'] = 'attachment;filename=服务器资产信息.xls'
                wb = xlwt.Workbook(encoding = 'utf-8')
                sheet = wb.add_sheet(u'服务器资产信息')

                alignment = xlwt.Alignment()
                alignment.horz = xlwt.Alignment.HORZ_LEFT
                alignment.vert = xlwt.Alignment.VERT_CENTER
                style = xlwt.XFStyle()
                style.alignment = alignment
                style.alignment.wrap = 1
                #1st line
                row0 = [u'主机名',u'操作系统',u'内核',u'Salt版本',u'ZeroMQ版本','Shell','Locale','SELinux',u'CPU型号',u'CPU线程',u'内存',u'硬盘分区',u'网络接口',u'平台',u'序列号',u'厂商型号',u'IDC机房']
                for i in range(0, len(row0)):
                    sheet.write(0,i,row0[i])
                    sheet.col(i).width = 6666

                export = request.GET.get('export')
                id_list = request.GET.getlist('id')
                row = 1
                if export == 'check':
                    for id in id_list:
                        serverasset = get_object_or_404(ServerAsset, pk=id)
                        SheetWrite(sheet, row, serverasset, style)
                        row = row + 1
                elif export == 'check_all':
                    for serverasset in ServerAsset.objects.all():
                        SheetWrite(sheet, row, serverasset, style)
                        row = row + 1
                output = StringIO.StringIO()
                wb.save(output)
                output.seek(0)
                response.write(output.getvalue())
                return response
        else:
            raise Http404
        return render(request, 'asset_server_list.html', {'all_server': all_server})

    if request.method == 'POST':
        if request.user.has_perm('asset.edit_asset'):
            field = request.POST.get('field')
            value = request.POST.get('value')
            if field == 'idc':
                value = idc[int(value)]
            value = str(value)
            id = request.POST.get('id')
            ServerAsset.objects.filter(id=id).update(**{field:value})
            return HttpResponse(value)
        else:
            raise Http404

@login_required
def idc_asset_manage(request,aid=None,action=None):
    """
    Manage IDC
    """
    if request.user.has_perms(['asset.view_asset', 'asset.edit_asset']):
        page_name = ''
        if aid:
            idc_list = get_object_or_404(IdcAsset, pk=aid)
            if action == 'edit':
                page_name = '编辑IDC机房'
            if action == 'delete':
                idc_list.delete()
                return redirect('idc_asset_list')
        else:
            idc_list = IdcAsset()
            action = 'add'
            page_name = '新增IDC机房'

        if request.method == 'POST':
            form = IdcAssetForm(request.POST,instance=idc_list)
            if form.is_valid():
                if action == 'add':
                    form.save()
                    return redirect('idc_asset_list')
                if action == 'edit':
                    form.save()
                    return redirect('idc_asset_list')
        else:
            form = IdcAssetForm(instance=idc_list)

        return render(request, 'asset_idc_manage.html', {"form":form, "page_name":page_name, "action":action})
    else:
        raise Http404

@login_required
def idc_asset_list(request):
    """
    IDC列表、IDC详细
    """
    if request.user.has_perm('asset.view_asset'):
        if request.method == 'GET':
            if request.GET.has_key('aid'):
                aid = request.get_full_path().split('=')[1]
                idc_detail = IdcAsset.objects.filter(id=aid)
                return render(request, 'asset_idc_detail.html', {'idc_detail': idc_detail})

        all_idc = IdcAsset.objects.all()

        return render(request, 'asset_idc_list.html', {'all_idc_list': all_idc})
    else:
        raise Http404

@login_required
def geo_input(request):
    if request.user.is_superuser:
        if request.method == 'POST':
            if request.is_ajax():
                GeoInput()
                return HttpResponse(json.dumps('Loaded!'))
    return redirect('idc_asset_list')
