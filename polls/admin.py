# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import Question, Person, Choice, RedisInfo, Post, NginxAcess, FileUpload, Ipaddr, RedisApply
from django.contrib.admin.models import LogEntry
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
    save_on_top = False

    # def redisCount(self, obj):
    #     return obj.redis_type.count()
    # redisCount.short_description = "Redis 数量"

    class Media:
        css = {
            'all': (
                "https://cdn.bootcss.com/bootstrap/4.0.0-beta.2/css/bootstrap.min.css",
            ),
        }
        js = ("https://cdn.bootcss.com/bootstrap/4.0.0-beta.2/js/bootstrap.bundle.js",)


class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'pub_date')


class NginxAcessAdmin(admin.ModelAdmin):
    list_display = ('ipaddr', 'date', 'count')


class logEntryAdmin(admin.ModelAdmin):
    list_display = ['object_repr', 'object_id', 'action_flag', 'user', 'change_message']


class IpaddrAdmin(admin.ModelAdmin):
    list_display = ['ip', 'area', 'machina_type', 'machina_mem', 'used_mem', 'used_cpu']
    list_filter = ['area']
    search_fields = ['ip']


class RedisApplyAdmin(admin.ModelAdmin):
    list_display = ['ins_name', 'ins_disc', 'redis_type', 'redis_mem', 'sys_author', 'area', 'pub_date']
    list_filter = ['redis_type']
    search_fields = ['area']


admin.site.register(LogEntry, logEntryAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(RedisInfo, RedisAdmin)
admin.site.register(NginxAcess, NginxAcessAdmin)
admin.site.register(Ipaddr, IpaddrAdmin)
admin.site.register(RedisApply, RedisApplyAdmin)