# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
import subprocess
from .models import Question, Choice
from django.http import Http404
from django.urls import reverse


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
    return HttpResponse("{} {} {}".format(year, month, slug))
