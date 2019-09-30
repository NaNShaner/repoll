# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
import datetime
from django.db import models
from django.utils import timezone
from django import forms
from captcha.fields import CaptchaField


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


class NameForm(forms.Form):
    your_name = forms.CharField(label='Your name', max_length=100)


class RedisInfo(models.Model):
    sys_type = models.CharField(max_length=5, unique=True)
    type_choice = [
        (0, "哨兵"),
        (1, "集群")
    ]
    redis_type = models.IntegerField(choices=type_choice)
    redis_port = models.IntegerField(verbose_name="Redis 端口", default=6379)
    pub_date = models.DateTimeField('date published')
    host_ip = models.CharField(max_length=50, default="请输入ip")

    def __str__(self):
        return self.sys_type


class Post(models.Model):
    title = models.CharField(max_length=200)
    slug = models.CharField(max_length=200)
    body = models.TextField()
    now = timezone.now()
    pub_date = models.DateTimeField(default=now)
    captcha = CaptchaField()

    class Meta:
        ordering = ('-pub_date', )

    def __unicode__(self):
        return self.title

    def __str__(self):
        return self.title


class NginxAcess(models.Model):
    ipaddr = models.CharField(max_length=16)
    date = models.DateTimeField('date published')
    count = models.IntegerField()

    def __str__(self):
        return self.ipaddr


class FileUpload(models.Model):
    file_name = models.FileField(upload_to='upload/', verbose_name=u"文件名称", default="文件")

