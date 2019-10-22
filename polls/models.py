# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
import datetime
from django.db import models
from django.utils import timezone
from django import forms
from django.utils.html import format_html
#from captcha.fields import CaptchaField
from django.contrib.auth.models import User


class Ipaddr(models.Model):
    ip = models.GenericIPAddressField(verbose_name="服务器IP")
    area = models.CharField(max_length=50, verbose_name="机房")
    choice_list = [
        (0, '虚拟机'),
        (1, "物理机")
    ]
    machina_type = models.IntegerField(choices=choice_list, verbose_name="机器类型")
    machina_mem = models.CharField(max_length=50, verbose_name="内存大小")
    used_mem = models.CharField(max_length=50, verbose_name="已分配内存")
    used_cpu = models.CharField(max_length=50, verbose_name="CPU使用率")

    def __str__(self):
        return self.ip

    class Meta:
        verbose_name = "资源池服务器列表"


class RedisInfo(models.Model):
    sys_type = models.CharField(max_length=5, unique=True)
    type_choice = [
        (0, "哨兵"),
        (1, "集群"),
        (2, "单机")
    ]
    redis_type = models.IntegerField(choices=type_choice)
    redis_port = models.IntegerField(verbose_name="Redis 端口", default=6379)
    pub_date = models.DateTimeField('date published')
    host_ip = models.ForeignKey(Ipaddr, on_delete=models.CASCADE)

    class Meta:
        ordering = ('-pub_date', )
        verbose_name = "Redis实例信息"

    def __str__(self):
        return self.sys_type


class RedisApply(models.Model):
    ins_name = models.CharField(max_length=50, verbose_name="应用名称")
    ins_disc = models.CharField(max_length=150, verbose_name="应用描述")
    type_choice = [
        (0, "哨兵"),
        (1, "集群"),
        (2, "单机")
    ]
    redis_type = models.IntegerField(choices=type_choice, verbose_name="存储种类")
    redis_mem = models.CharField(max_length=50, help_text="例如填写：512M,1G,2G..32G等", verbose_name="内存总量")
    sys_author = models.CharField(max_length=50, verbose_name="项目负责人")
    area = models.CharField(max_length=50, verbose_name="机房")
    pub_date = models.DateTimeField('申请时间', default=timezone.now)
    create_user = models.CharField(max_length=150, null=True, verbose_name="申请人")
    status_choice = [
        (0, "申请中"),
        (1, "已审批"),
        (2, "已拒绝"),
    ]
    apply_status = models.IntegerField(choices=status_choice, default=status_choice[0][0], blank=True, null=True,
                                       verbose_name="申请状态")

    class Meta:
        ordering = ('-pub_date', )
        verbose_name = "Redis实例申请"

    def __str__(self):
        return self.ins_name


class RedisIns(models.Model):
    ins_name = models.CharField(max_length=50, unique=True, verbose_name="应用名称")
    ins_disc = models.CharField(max_length=150, verbose_name="应用描述")
    type_choice = [
        (0, "哨兵"),
        (1, "集群"),
        (2, "单机")
    ]
    redis_type = models.IntegerField(choices=type_choice, verbose_name="存储种类")
    redis_mem = models.CharField(max_length=50, help_text="例如填写：512M,1G,2G..32G等", verbose_name="内存总量")
    sys_author = models.CharField(max_length=50, verbose_name="项目负责人")
    area = models.CharField(max_length=50, verbose_name="机房")
    pub_date = models.DateTimeField('审批时间', default=timezone.now)
    approval_user = models.CharField(max_length=150, null=True, verbose_name="审批人")
    ins_choice = [
        (0, "已上线"),
        (1, "已下线"),
        (2, "未审批"),
        (3, "已拒绝"),
    ]
    ins_status = models.IntegerField(choices=ins_choice, default=ins_choice[2][0], blank=True, verbose_name="实例状态")
    ipaddr = models.ForeignKey(Ipaddr, on_delete=models.CASCADE, null=True)
    apply_text = models.TextField(max_length=250, verbose_name="实例详情", blank=True, null=True)

    class Meta:
        ordering = ('-pub_date', )
        verbose_name = "Redis实例信息"

    def colored_name(self):
        return format_html(
            '<span style="color: #{};">{} {}</span>',
            self.ins_status,
        )

    def __str__(self):
        return self.ins_name


class Production(forms.ModelForm):
    name = forms.CharField(max_length=50, label="名字", error_messages={'required': "不能为空"})
    weight = forms.CharField(max_length=50, label="重量")
    size = forms.CharField(max_length=50, label="尺寸")
    AI = forms.BooleanField(label="智能机", initial=True)
    choice_list = [
        (0, '华为'),
        (1, "苹果"),
        (2, "OPPO")
    ]
    type = forms.ChoiceField(choices=choice_list, label="型号")


class RedisVersion(models.Model):
    redis_version = models.CharField(max_length=60, unique=True, primary_key=True,
                                     default="3.0.6", verbose_name="Redis版本", error_messages={'required': "不能为空"})
    pub_date = models.DateTimeField(default=timezone.now, verbose_name="版本发布时间")
    who_apply_ver = models.CharField(max_length=50, verbose_name="版本发布人")

    def __str__(self):
        return self.redis_version

    class Meta:
        ordering = ('-pub_date', )
        verbose_name = "RedisVersion"
        verbose_name_plural = "Redis版本视图"


class RedisModel(models.Model):
    choice_list = [
        ('Redis-Standalone', 'Redis-Standalone'),
        ('Redis-Cluster', 'Redis-Cluster'),
        ('Redis-Sentinel', 'Redis-Sentinel')
    ]
    redis_type_models = models.CharField(max_length=150, choices=choice_list, unique=True,
                                         default=choice_list[0][0], verbose_name="Redis运行模式")

    def __str__(self):
        return self.redis_type_models

    class Meta:
        verbose_name = "Redis模式视图"


class RedisConf(models.Model):
    redis_type = models.OneToOneField(RedisModel, default=RedisModel.choice_list[0][1], unique=True,
                                      to_field='redis_type_models',
                                      on_delete=models.CASCADE)
    redis_version = models.ForeignKey(RedisVersion, on_delete=models.CASCADE)
    pub_date = models.DateTimeField("配置发布时间")
    who_apply = models.CharField(max_length=50, verbose_name="配置发布人")
    choice_list = [
        (0, '无效'),
        (1, "有效")
    ]
    redis_port = models.IntegerField(default=6379, verbose_name="端口")
    redis_mem = models.CharField(max_length=150, default="64m", verbose_name="内存大小")
    redis_daemonize = models.CharField(max_length=30, default="no", verbose_name="是否守护进程")
    tcp_backlog = models.IntegerField(default=511, help_text="TCP连接完成队列", verbose_name="tcp-backlog")
    timeout = models.IntegerField(default=0, help_text="客户端闲置多少秒后关闭连接,默认为0,永不关闭", verbose_name="timeout")
    tcp_keepalive = models.IntegerField(default=60, help_text="检测客户端是否健康周期,默认关闭", verbose_name="tcp-keepalive")
    loglevel = models.CharField(max_length=50, default="notice", help_text="日志级别", verbose_name="loglevel")
    databases = models.IntegerField(help_text="可用的数据库数，默认值为16个,默认数据库为0", verbose_name="databases", default=16)
    appendonly = models.CharField(max_length=150, help_text="开启append only持久化模式", verbose_name="appendonly", default="yes")

    def __str__(self):
        return self.redis_version

    class Meta:
        ordering = ('-pub_date', )
        verbose_name = "Redis配置信息"
