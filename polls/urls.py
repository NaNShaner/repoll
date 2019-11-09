#!/usr/bin/python

# -*- coding:UTF-8 -*-

from django.urls import path
from . import views
from django.conf.urls import url, include
from polls.apis import redisstop, redisstart


app_name = 'polls'
urlpatterns = [
    path('redis_qps/<str:ins_id>/', views.redis_qps, name='redis_qps'),
    path(r'apis/redis-stop/<str:ins_id>/', redisstop),
    path(r'apis/redis-start/<str:ins_id>/', redisstart),
]