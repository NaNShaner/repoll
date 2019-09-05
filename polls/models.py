# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
import datetime
from django.db import models
from django.utils import timezone


class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')

    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now

    def __str__(self):
        return self.question_text


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=300)
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.choice_text


class Person(models.Model):
    name = models.CharField(max_length=5, unique=True)
    sex_choice = [
        (0, "男"),
        (1, "女")
    ]
    sex = models.IntegerField(choices=sex_choice)
    upload = models.FileField(upload_to='uploads/')
    image = models.ImageField(help_text="只能上传图片")
    email_filed = models.EmailField(default='test@test.com')

    def __str__(self):
        return self.name, self.sex


class RedisInfo(models.Model):
    sys_type = models.CharField(max_length=5, unique=True)
    type_choice = [
        (0, "哨兵"),
        (1, "集群")
    ]
    redis_type = models.IntegerField(choices=type_choice)
    redis_port = models.IntegerField(verbose_name="Redis 端口", default=6379)
    pub_date = models.DateTimeField('date published')


    def __str__(self):
        return self.sys_type
