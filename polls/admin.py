# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import Question, Person, Choice, RedisInfo, Post, NginxAcess, FileUpload, Ipaddr, RedisApply, RedisIns
from django.contrib.admin.models import LogEntry
# Register your models here.
from .handlers import ApproveRedis


class MyAdminSite(admin.AdminSite):
    site_header = 'Redis云管系统'  # 此处设置页面显示标题
    site_title = '运维管理'  # 此处设置页面头部标题


admin.site = MyAdminSite(name='management')


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

    def get_queryset(self, request):
        """函数作用：使当前登录的用户只能看到自己负责的服务器"""
        qs = super(RedisApplyAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=RedisApply.objects.filter(approval_user=request.user))

    list_display = ['ins_name', 'ins_disc', 'redis_type',
                    'redis_mem', 'sys_author', 'area',
                    'pub_date', 'create_user', 'apply_status']
    list_filter = ['redis_type']
    search_fields = ['area']
    # date_hierarchy = 'go_time'
    actions = ['approve_selected_new_assets', 'deny_selected_new_assets']

    def approve_selected_new_assets(self, request, queryset):
        """
        用于在申请redis的界面添加一个审批通过按钮
        :param request: Http Request实例
        :param queryset: 勾选实例名称
        :return:
        """
        # 获得被打钩的checkbox对应的Redis的id编号，用于更新数据库的主键
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        success_upline_number = 0
        try:
            for asset_id in selected:
                # print(selected)
                obj = ApproveRedis(request, asset_id)
                create_redis_ins = obj.create_asset()
                if create_redis_ins:
                    success_upline_number += 1
                    self.message_user(request, "成功批准  %s  个新Redis实例上线！" % success_upline_number)
                    obj.redis_apply_status_update()
                else:
                    self.message_user(request, "实例为 {0} 的实例上线失败".format(queryset))
        except ValueError as e:
            self.message_user(request, "实例为 {0} 的实例上线失败，原因为{1}".format(queryset, e))
    approve_selected_new_assets.short_description = "批准选择的Redis实例"

    def deny_selected_new_assets(self, request, queryset):
        """
        用于在申请redis的界面添加一个审批拒绝按钮
        :param request: Http Request实例
        :param queryset: 勾选实例名称
        :return:
        """
        # 获得被打钩的checkbox对应的Redis的id编号，用于更新数据库的主键
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        deny_upline_number = 0
        try:
            for asset_id in selected:
                # print(selected)
                obj = ApproveRedis(request, asset_id)
                deny_redis_ins = obj.deny_create()
                if deny_redis_ins:
                    deny_upline_number += 1
                    self.message_user(request, "已拒绝  %s  个新Redis实例上线！" % deny_upline_number)
        except ValueError as e:
            self.message_user(request, "操作实例为 {0} 的实例失败，原因为{1}".format(queryset, e))
    deny_selected_new_assets.short_description = "拒绝选择的Redis实例"


class RedisApprovalAdmin(admin.ModelAdmin):
    list_display = ['ins_name', 'ins_disc', 'redis_type',
                    'redis_mem', 'sys_author', 'area',
                    'pub_date', 'approval_user', 'ins_status',
                    ]
    list_filter = ['redis_type']
    search_fields = ['area', 'ins_status']

    def colored_status(self, request):
        pass


admin.site.register(LogEntry, logEntryAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(RedisInfo, RedisAdmin)
admin.site.register(NginxAcess, NginxAcessAdmin)
admin.site.register(Ipaddr, IpaddrAdmin)
admin.site.register(RedisApply, RedisApplyAdmin)
admin.site.register(RedisIns, RedisApprovalAdmin)