# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import *
from django.contrib.admin.models import LogEntry

# Register your models here.
from .handlers import ApproveRedis


class MyAdminSite(admin.AdminSite):
    site_header = 'Redis云管系统'  # 此处设置页面显示标题
    site_title = '运维管理'  # 此处设置页面头部标题


admin.site = MyAdminSite(name='management')


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


class logEntryAdmin(admin.ModelAdmin):
    list_display = ['object_repr', 'object_id', 'action_flag', 'user', 'change_message']


class IpaddrAdmin(admin.ModelAdmin):
    list_display = ['id', 'ip', 'area', 'machina_type', 'machina_mem', 'used_mem', 'used_cpu']
    list_filter = ['area']
    search_fields = ['ip']


class RedisVersionAdmin(admin.ModelAdmin):
    list_display = ['redis_version', 'who_apply', 'pub_date']
    list_filter = ['redis_version']
    search_fields = ['who_apply']


class RedisConfAdmin(admin.ModelAdmin):
    list_display = ['redis_version', 'who_apply', 'pub_date']
    list_filter = ['redis_version']
    search_fields = ['who_apply']


class RedisModelAdmin(admin.ModelAdmin):
    list_display = ['redis_type_models']
    list_filter = ['redis_type_models']
    search_fields = ['redis_type_models']


class ChoiceInline(admin.StackedInline):
    model = ApplyRedisText
    extra = 1


class RealTimeQpsInline(admin.StackedInline):
    model = RealTimeQps
    extra = 1


class RedisApplyAdmin(admin.ModelAdmin):

    def get_queryset(self, request):
        """函数作用：使当前登录的用户只能看到自己负责的服务器"""
        qs = super(RedisApplyAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=RedisApply.objects.filter(approval_user=request.user))

    list_display = ['id', 'apply_ins_name', 'ins_disc', 'redis_type',
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
    list_display = ['id', 'redis_ins_name', 'ins_disc', 'redis_type',
                    'redis_mem', 'sys_author', 'area',
                    'pub_date', 'approval_user', 'ins_status'
                    ]
    list_filter = ['redis_type']
    search_fields = ['area', 'ins_status']
    actions = ['apply_selected_new_redis', 'deny_selected_new_redis']
    inlines = [ChoiceInline]

    # def colored_status(self, request):
    #     pass
    #
    def return_message(self, request, queryset, mem=None):
        self.message_user(request, "操作实例为 {0} 的实例失败，原因为{1}".format(queryset, mem))


class RunningInsTimeAdmin(admin.ModelAdmin):
    list_display = ['id', 'running_ins_name', 'redis_type', 'redis_ip', 'running_ins_port', 'redis_ins_mem']
    list_filter = ['running_ins_name']
    search_fields = ['redis_type']
    inlines = [RealTimeQpsInline]


admin.site.register(LogEntry, logEntryAdmin)
admin.site.register(Ipaddr, IpaddrAdmin)
admin.site.register(RedisApply, RedisApplyAdmin)
admin.site.register(RedisIns, RedisApprovalAdmin)
admin.site.register(RedisVersion, RedisVersionAdmin)
admin.site.register(RedisConf, RedisConfAdmin)
admin.site.register(RedisModel, RedisModelAdmin)
admin.site.register(RunningInsTime, RunningInsTimeAdmin)
admin.site.register(RealTimeQps)