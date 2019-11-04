# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, get_object_or_404, redirect, render_to_response
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
import subprocess
from .models import RedisInfo, RedisApply, RealTimeQps, RunningInsTime
from django.http import Http404
from django.urls import reverse
#from django.db import models
from django.utils import timezone
from django.template.loader import get_template
from datetime import datetime
import redis
import os
import time
import csv
from django.views.decorators.csrf import csrf_exempt
from .models import forms
from rest_framework.decorators import api_view
from .form import NameForm

# pyecharts
import json
from jinja2 import Environment, FileSystemLoader
from pyecharts.globals import CurrentConfig
from django.http import HttpResponse

CurrentConfig.GLOBAL_ENV = Environment(loader=FileSystemLoader("./templates/polls"))
from pyecharts import options as opts
from pyecharts.charts import Bar, Line
from pyecharts.faker import  Faker

from random import randrange
from rest_framework.views import APIView


# Create your views here.


def redisApproval(request):
    obj = RedisApply.objects.order_by('-pub_date')[:5]
    # template =get_template("polls/redis_list.html")
    # html = template.render(locals())
    context = {
        "redis_list": obj
    }

    return render(request, 'polls/redis_list.html', context)


def run_scan_tomcat(request, apptrye):
    if apptrye == 'tomcat':
        ex = subprocess.getstatusoutput("/opt/pycharm/tomcat/dist/get_tomcat_ci_pro")
        return HttpResponse(ex[1])
    else:
        return HttpResponse("当前入参错误，apptype为%s" % apptrye)


# echarts
def pyecharts(request):
    real_time_qps = RealTimeQps.objects.all()
    redis_ins_id = list(set([redis_ins_id.__dict__['redis_running_monitor_id'] for redis_ins_id in real_time_qps]))
    for ins_id in redis_ins_id:
        real_time_obj = real_time_qps.filter(redis_running_monitor_id=ins_id).order_by('-collect_date')[:60]
        real_time = [real_time.__dict__['collect_date'] for real_time in real_time_obj]
        redis_qps = [redis_qps.__dict__['redis_qps'] for redis_qps in real_time_obj]
        c = (
            Bar()
            .add_xaxis(real_time)
            .add_yaxis("商家A", redis_qps)
            .set_global_opts(title_opts=opts.TitleOpts(title="Bar-基本示例", subtitle="毕井锐"),
                             toolbox_opts=opts.ToolboxOpts(),
                             datazoom_opts=[opts.DataZoomOpts(), opts.DataZoomOpts(type_="inside")],)
        )
        return HttpResponse(c.render_embed())


def line_base(request):
    real_time_qps = RealTimeQps.objects.all()
    running_ins_time = RunningInsTime.objects.all()
    redis_ins_id = list(set([redis_ins_id.__dict__['redis_running_monitor_id'] for redis_ins_id in real_time_qps]))
    for ins_id in redis_ins_id:
        real_time_obj = real_time_qps.filter(redis_running_monitor_id=ins_id).order_by('-collect_date')[:60]
        # redis_ins = real_time_qps.filter(redis_running_monitor_id=ins_id).values('redis_running_monitor_id').first()
        running_ins = running_ins_time.filter(id=ins_id)
        running_ins_name = running_ins.values('running_ins_name').first()
        running_ins_ip = running_ins.values('redis_ip').first()
        running_ins_port = running_ins.values('running_ins_port').first()
        real_time = [real_time.__dict__['collect_date'] for real_time in real_time_obj]
        redis_qps = [redis_qps.__dict__['redis_qps'] for redis_qps in real_time_obj]
        c = (
            Line()
            .add_xaxis(real_time)
            .add_yaxis(running_ins_name['running_ins_name'], redis_qps, is_smooth=True)
            .set_global_opts(title_opts=opts.TitleOpts(title="{0}:{1}".format(running_ins_ip['redis_ip'],
                                                                              running_ins_port['running_ins_port']),
                                                       subtitle="Redis QPS图"),
                             toolbox_opts=opts.ToolboxOpts(),
                             datazoom_opts=[opts.DataZoomOpts(), opts.DataZoomOpts(type_="inside")],)
        )
        return HttpResponse(c.render_embed())


# def list(request):
#     test = Question.objects.all()
#     return render(request, 'polls/list.html', {"b": test})


# @api_view(http_method_names=['GET', 'POST'])
# def redis_exec(request):
#     j = json.loads(request.body)
#     appname = j.get('appName')
#     type = j.get('type')
#     port = j.get('port')
#     t = timezone.now()
#     b = RedisInfo(sys_type=appname, redis_type=type, redis_port=port, pub_date=t)
#     b.save()
#     return HttpResponse(b)

@api_view(http_method_names=['GET', 'POST'])
def redis_exec(request):
    appname = request.GET.get('appName')
    type = request.GET.get('type')
    port = request.GET.get('port')
    ipaddr = request.GET.get('ip')
    if type == '0':
        _cmd = "ssh -l root " + ipaddr + " " + "\" redis-server \" " + "--port" + port
        _ex_cmd = subprocess.getstatusoutput(_cmd)
        print(_ex_cmd)
        t = timezone.now()
        b = RedisInfo(sys_type=appname, redis_type=type, redis_port=port, pub_date=t, host_ip=ipaddr)
        b.save()
        return HttpResponse(_ex_cmd[1])
    return HttpResponse("Redis 启动失败")


def get_name(request):
    # 如果form通过POST方法发送数据
    if request.method == 'POST':
        # 接受request.POST参数构造form类的实例
        form = NameForm(request.POST)
        # 验证数据是否合法
        if form.is_valid():
            # 处理form.cleaned_data中的数据
            # ...
            # 重定向到一个新的URL
            return HttpResponseRedirect('/thanks/')

    # 如果是通过GET方法请求数据，返回一个空的表单
    else:
        form = NameForm()
    return render(request, 'polls/name.html', {'form': form})


def return_name(request):
    return render(request, 'polls/your-name.html', {'your-name': "毕井锐"})


# def homepage(request):
#     template = get_template('polls/blog_index.html')
#     posts = Post.objects.all()
#     now = datetime.now()
#     hour = now.timetuple().tm_hour
#     a = locals()
#     html = template.render(locals())
#     return HttpResponse(html)
#
#
# def showpost(request, slug):
#     template = get_template('polls/blog.html')
#     try:
#         post = Post.objects.get(slug=slug)
#         if post is not None:
#             html = template.render(locals())
#             return HttpResponse(html)
#     except:
#         return redirect('/')

#
# def run_nginx_log(request):
#     ls  = os.listdir("/Users/bijingrui/PycharmProjects/mysite/upload")
#     # obj = NginxAcess.objects
#     start = time.time()
#     if ls:
#         for file in ls:
#             if "log" in file:
#                 with open("/Users/bijingrui/PycharmProjects/mysite/upload/" + file) as f:
#                     for line in f:
#                         ipaddr = line.split()[0]
#                         date1 = line.split()[3].replace("[", "").replace("Sep", "9").replace("/",":").split(":")
#                         date = date1[2] + "-" + date1[1] + "-" + date1[0] + " " + date1[3] + ":" + date1[4] + ":" + date1[5]
#                         obj = NginxAcess(ipaddr=ipaddr, date=date, count="1")
#                         obj.save()
#     end = time.time()
#     t = end - start
#     return HttpResponse("文件解析入库成功，耗时{0}".format(t))


@csrf_exempt
def test_api(request):
    return JsonResponse({"result": 0, "msg": "sucess"})


def downlad(request):
    respose = HttpResponse(content_type='text/csv')
    respose['Conent-Dispostion'] = 'attachment; filename="somefilename.csv"'
    writer = csv.writer(respose)
    writer.writerow(['First Row', 'A', 'B', 'C'])
    return respose


def login(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        return redirect('/')
    else:
        if request.GET.get('name'):
            name = request.GET.get('name')
        else:
            name = 'Everyone'
        return HttpResponse('username is {0}'.format(name))


def favicon(request):
    img = "static/favicon.ico"
    image_date = open(img, "rb").read()
    return HttpResponse(image_date, content_type='image/jpg')


def redisLogin(request):
    return render_to_response('polls/redis_info.html')

