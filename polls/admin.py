# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import Question, Person, Choice, RedisInfo, Post, NginxAcess, FileUpload

# Register your models here.

admin.site.register(Choice)
admin.site.register(Person)
admin.site.register(FileUpload)



class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2


class RedisInline(admin.TabularInline):
    model = RedisInfo
    extra = 2


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'pub_date', 'was_published_recently')
    list_filter = ['pub_date']
    search_fields = ['question_text']
    fieldsets = [
        (None, {'fields': ['question_text']}),
        ('Date infomation', {'fields': ['pub_date']}),
    ]
    inlines = [ChoiceInline]


class RedisAdmin(admin.ModelAdmin):
    list_display = ('sys_type', 'redis_type', 'host_ip', 'redis_port', 'pub_date')
    list_filter = ['redis_type']
    search_fields = ['redis_type']
    fieldsets = [
        ('所属系统', {'fields': ['sys_type']}),
        ('Redis类型', {'fields': ['redis_type','pub_date']}),
        ('Redis信息', {'fields': ['host_ip', 'redis_port']}),
    ]
    # inlines = [RedisInline]


class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'pub_date')


class NginxAcessAdmin(admin.ModelAdmin):
    list_display = ('ipaddr', 'date', 'count')


admin.site.register(Post, PostAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(RedisInfo, RedisAdmin)
admin.site.register(NginxAcess, NginxAcessAdmin)