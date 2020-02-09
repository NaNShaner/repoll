#!/usr/bin/python

# -*- coding:UTF-8 -*-

from django.urls import path
from . import views
from django.conf.urls import url, include
from polls.apis import redisstop, redisstart, allredisins, memory_action

app_name = 'polls'
urlpatterns = [
    path('redis_qps/<str:redis_type>/<str:ins_id>/<str:redis_ip>/<str:redis_port>/', views.redis_qps, name='redis_qps'),
    path(r'apis/redis-stop/<str:redis_type>/<str:ins_id>/', redisstop),
    path(r'apis/redis-start/<str:redis_type>/<str:ins_id>/', redisstart),
    path(r'apis/redis-ins/<str:redis_type>/', allredisins),
    path(r'apis/redis-ins/<str:redis_type>/<str:redis_ins_name>/<str:memory>', memory_action)
]