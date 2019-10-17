# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, get_object_or_404, redirect, render_to_response
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
import subprocess
from .models import Question, Choice, RedisInfo, Production, RedisApply
from django.http import Http404
from django.urls import reverse
#from django.db import models
from .models import models as mo
from django.utils import timezone
from polls.models import NameForm, Post
from django.template.loader import get_template
from datetime import datetime
import redis
import os
import time
import csv
from django.views.decorators.csrf import csrf_exempt
from polls.models import NginxAcess
from .models import forms
from rest_framework.decorators import api_view
from .form import NameForm



#### pyecharts ####
import json
from jinja2 import Environment, FileSystemLoader
from pyecharts.globals import CurrentConfig
from django.http import HttpResponse

CurrentConfig.GLOBAL_ENV = Environment(loader=FileSystemLoader("./templates/polls"))
from pyecharts import options as opts
from pyecharts.charts import Bar
from random import randrange
from rest_framework.views import APIView


# Create your views here.


def index(request):
    latest_question_list = Question.objects.order_by('-pub_date')[:5]
    # template = loader.get_template('polls/index.html')
    context = {
        'latest_question_list': latest_question_list
    }
    # return HttpResponse(template.render(context, request))
    return render(request, 'polls/index.html', context)


def redisApproval(request):
    obj = RedisApply.objects.order_by('-pub_date')[:5]
    # template =get_template("polls/redis_list.html")
    # html = template.render(locals())
    context = {
        "redis_list": obj
    }

    return render(request, 'polls/redis_list.html', context)


def detail(request, question_id):
    # try:
    #     question = Question.objects.get(pk=question_id)
    # except Question.DoesNotExist:
    #     raise Http404("问卷不存在")
    question = get_object_or_404(Question, pk=question_id)
    return render(request, 'polls/detail.html', {"question": question})


def results(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, 'polls/results.html', {"question": question})


def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except(KeyError, Choice.DoesNotExist):
        return render(request, 'polls/detail.html', {
            "question": question,
            "error_message": "还没有任何选项"
        })
    else:
        selected_choice.votes += 1
        selected_choice.save()
        return HttpResponseRedirect(reverse('polls:results', args=(question_id,)))


def run_scan_tomcat(request, apptrye):
    if apptrye == 'tomcat':
        ex = subprocess.getstatusoutput("/opt/pycharm/tomcat/dist/get_tomcat_ci_pro")
        return HttpResponse(ex[1])
    else:
        return HttpResponse("当前入参错误，apptype为%s" % apptrye)


def url_test(request, year, month, slug):
    test = Question.objects.all()
    print(test)
    return HttpResponse("{} {} {}".format(year, month, slug))


# echarts
def pyecharts(request):
    obj = Choice.objects.get(id=1)
    print(obj)
    c = (
        Bar()
        .add_xaxis(["衬衫", "羊毛衫", "雪纺衫", "裤子", "高跟鞋", "袜子"])
        .add_yaxis("商家A", [5, 20, 36, 10, 75, 90])
        .add_yaxis("商家B", [15, 25, 16, 55, 48, 8])
        .set_global_opts(title_opts=opts.TitleOpts(title="Bar-基本示例", subtitle="毕井锐"))
    )
    return HttpResponse(c.render_embed())


def list(request):
    test = Question.objects.all()
    return render(request, 'polls/list.html', {"b": test})


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
        mo.Redis
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


def homepage(request):
    template = get_template('polls/blog_index.html')
    posts = Post.objects.all()
    now = datetime.now()
    hour = now.timetuple().tm_hour
    a = locals()
    html = template.render(locals())
    return HttpResponse(html)


def showpost(request, slug):
    template = get_template('polls/blog.html')
    try:
        post = Post.objects.get(slug=slug)
        if post is not None:
            html = template.render(locals())
            return HttpResponse(html)
    except:
        return redirect('/')


def run_nginx_log(request):
    ls  = os.listdir("/Users/bijingrui/PycharmProjects/mysite/upload")
    # obj = NginxAcess.objects
    start = time.time()
    if ls:
        for file in ls:
            if "log" in file:
                with open("/Users/bijingrui/PycharmProjects/mysite/upload/" + file) as f:
                    for line in f:
                        ipaddr = line.split()[0]
                        date1 = line.split()[3].replace("[", "").replace("Sep", "9").replace("/",":").split(":")
                        date = date1[2] + "-" + date1[1] + "-" + date1[0] + " " + date1[3] + ":" + date1[4] + ":" + date1[5]
                        obj = NginxAcess(ipaddr=ipaddr, date=date, count="1")
                        obj.save()
    end = time.time()
    t = end - start
    return HttpResponse("文件解析入库成功，耗时{0}".format(t))


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


def form(request):
    product = Production()
    return render(request, 'polls/form.html', locals())


def favicon(request):
    img = "static/favicon.ico"
    image_date = open(img, "rb").read()
    return HttpResponse(image_date, content_type='image/jpg')


def redisLogin(request):
    return render_to_response('polls/redis_info.html')

