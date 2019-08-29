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
    name = models.CharField(max_length=5)
    sex_choice = [
        (0, "男"),
        (1, "女")
    ]
    sex = models.IntegerField(choices=sex_choice)
    upload = models.FileField(upload_to='uploads/')
    email_filed = models.EmailField(default='test@test.com')

    def __str__(self):
        return self.name

