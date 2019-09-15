# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
import subprocess
from .models import Question, Choice, RedisInfo
from django.http import Http404
from django.urls import reverse
from django.db import models
from django.utils import timezone
from polls.models import NameForm, Post
from django.template.loader import get_template
from datetime import datetime


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


def redis_exec(request, appname, type, port):
    t = timezone.now()
    b = RedisInfo(sys_type=appname, redis_type=type, redis_port=port, pub_date=t)
    b.save()
    return HttpResponse(b)


def get_name(request):
    if request.method == 'POST':
        form = NameForm(request.POST)
        if form.is_valid():
            return HttpResponseRedirect('/thanks/')
    else:
        form = NameForm()
    return render(request, 'polls/name.html', {'form': form})


def return_name(request):
    return render(request, 'polls/your-name.html', {'your-name': "毕井锐"})


def homepage(request):
    # posts = Post.objects.all()
    # post_list = []
    # for count, post in enumerate(posts):
    #     post_list.append("No.{0}".format(str(count)+" "+str(post)+"<br>"))
    # return HttpResponse(post_list)
    template = get_template('polls/blog_index.html')
    posts = Post.objects.all()
    now = datetime.now()
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
