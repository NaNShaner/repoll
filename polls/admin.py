# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from inline_actions.admin import InlineActionsMixin
from inline_actions.admin import InlineActionsModelAdminMixin
from django.shortcuts import redirect
from .models import *
from django.contrib.admin.models import LogEntry
from jinja2 import Environment, FileSystemLoader
from .handlers import ApproveRedis
from pyecharts.globals import CurrentConfig
CurrentConfig.GLOBAL_ENV = Environment(loader=FileSystemLoader("./templates/polls"))

# 此处设置页面显示标题
admin.site.site_header = 'Redis云管系统'

# 此处设置页面头部标题
admin.site.site_title = 'Redis云管系统'
admin.site.index_title = 'Repoll'


class RedisAdmin(admin.ModelAdmin):
    list_display = ('sys_type', 'redis_type', 'host_ip', 'redis_port', 'pub_date')
    list_filter = ['redis_type']
    search_fields = ['redis_type']
    fieldsets = [
        ('所属系统', {'fields': ['sys_type']}),
        ('Redis类型', {'fields': ['redis_type', 'pub_date']}),
        ('Redis信息', {'fields': ['host_ip', 'redis_port']}),
    ]
    save_on_top = False


class LogEntryAdmin(admin.ModelAdmin):
    list_display = ['object_repr', 'object_id', 'action_flag', 'user', 'change_message']


class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'password', 'email', 'is_staff', 'is_active']


class IpaddrAdmin(admin.ModelAdmin):
    list_display = ['id', 'ip', 'area', 'machina_type', 'machina_mem', 'used_mem', 'used_cpu']
    list_filter = ['area']
    search_fields = ['ip']


class RedisVersionAdmin(admin.ModelAdmin):
    list_display = ['redis_version', 'who_apply', 'pub_date']
    list_filter = ['redis_version']
    search_fields = ['who_apply']


class RedisConfControlAdmin(admin.ModelAdmin):
    list_display = ['redis_version', 'who_apply', 'pub_date']
    list_filter = ['redis_version']
    search_fields = ['who_apply']


class RedisConfAdmin(admin.ModelAdmin):
    list_display = ['id', 'redis_version']


class RedisModelAdmin(admin.ModelAdmin):
    list_display = ['redis_type_models']
    list_filter = ['redis_type_models']
    search_fields = ['redis_type_models']


class ChoiceInline(admin.StackedInline):
    model = ApplyRedisText
    extra = 1


class RunningInsStandaloneInline(InlineActionsMixin, admin.TabularInline):
    model = RunningInsStandalone
    inline_actions = ['redis_start', 'redis_stop', 'redis_qps']

    def has_delete_permission(self, request, obj=None):
        """隐藏删除按钮"""
        return False

    def redis_start(self, request, obj, parent_obj):
        """启动redis"""
        button_html = "/polls/apis/redis-start/{0}/{1}/".format('standalone', obj.id)
        return redirect(button_html)

    def redis_stop(self, request, obj, parent_obj):
        """停止redis"""
        if isinstance(obj, RunningInsStandalone):
            button_html = "/polls/apis/redis-stop/{0}/{1}/".format('standalone', obj.id)
            return redirect(button_html)

    def redis_qps(self, request, obj, parent_obj):
        """redis qps"""
        button_html = "/polls/redis_qps/{0}/{1}/{2}/{3}".format('standalone', parent_obj.id, obj.redis_ip, obj.running_ins_port)
        return redirect(button_html)

    readonly_fields = ['id', 'running_ins_name', 'redis_type', 'redis_ip', 'running_ins_port', 'redis_ins_mem']


class RunningInsSentinelInline(InlineActionsMixin, admin.TabularInline):
    model = RunningInsSentinel

    def has_delete_permission(self, request, obj=None):
        """隐藏删除按钮"""
        return False

    def redis_start(self, request, obj, parent_obj):
        """启动redis"""
        button_html = "/polls/apis/redis-start/{0}/{1}/".format('sentinel', obj.id)
        return redirect(button_html)

    def redis_stop(self, request, obj, parent_obj):
        """
        停止redis
        """
        if isinstance(obj, RunningInsSentinel):
            button_html = "/polls/apis/redis-stop/{0}/{1}/".format('sentinel', obj.id)
            return redirect(button_html)

    def redis_qps(self, request, obj, parent_obj):
        """
        显示redis_qps
        """
        if obj.redis_type != 'Redis-Sentinel':
            button_html = "/polls/redis_qps/{0}/{1}/{2}/{3}".format('sentinel', parent_obj.id, obj.redis_ip, obj.running_ins_port)
            return redirect(button_html)

    def get_inline_actions(self, request, obj=None):
        """
        针对redis sentinel模式不显示redis_qps的按钮
        """
        if obj.redis_type != 'Redis-Sentinel':
            self.inline_actions = ['redis_start', 'redis_stop', 'redis_qps']
        else:
            self.inline_actions = ['redis_start', 'redis_stop', ]
        return self.inline_actions
    readonly_fields = ['id', 'running_ins_name', 'redis_type', 'redis_ip', 'running_ins_port', 'redis_ins_mem']


class RealTimeQpsInline(admin.StackedInline):
    model = RealTimeQps
    extra = 1


class ApplyRedisInfoAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        """函数作用：使当前登录的用户只能看到自己负责的实例"""
        qs = super(ApplyRedisInfoAdmin, self).get_queryset(request)
        result = qs.filter(create_user=request.user)
        if request.user.is_superuser:
            return qs
        return result

    def save_model(self, request, obj, form, change):
        """
        隐藏前端页面申请用户字段，后台自动添加用户入库
        :param request: 当前wsgi
        :param obj:
        :param form:
        :param change:
        :return:
        """
        obj.create_user = request.user
        super().save_model(request, obj, form, change)

    list_display = ['id', 'apply_ins_name', 'ins_disc', 'redis_type',
                    'redis_mem', 'sys_author', 'area',
                    'pub_date', 'apply_status']
    list_filter = ['redis_type']
    search_fields = ['area']
    # 不可见字段
    exclude = ['create_user']
    list_per_page = 15

    readonly_fields = ['apply_status', ]


class RedisApplyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        """
        禁用添加按钮
        :param request:
        :return:
        """
        return False

    def has_delete_permission(self, request, obj=None):
        """
        禁用删除按钮
        :param request:
        :param obj:
        :return:
        """
        return False

    def get_actions(self, request):
        """
        在actions中去掉‘删除’操作
        :param request:
        :return:
        """
        actions = super(RedisApplyAdmin, self).get_actions(request)
        if request.user.username[0].upper() != 'J':
            if 'delete_selected' in actions:
                del actions['delete_selected']
        return actions

    def get_queryset(self, request):
        """函数作用：使当前登录的用户只能看到自己负责的实例"""
        qs = super(RedisApplyAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(create_user=RedisApply.objects.filter(create_user=request.user))


    list_display = ['id', 'apply_ins_name', 'ins_disc', 'redis_type',
                    'redis_mem', 'sys_author', 'area',
                    'pub_date', 'create_user', 'apply_status']
    list_filter = ['redis_type']
    search_fields = ['area']
    list_per_page = 15
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
                obj = ApproveRedis(request, asset_id)
                create_redis_ins = obj.create_asset()
                if create_redis_ins:
                    success_upline_number += 1
                    self.message_user(request, "成功批准  %s  个新Redis实例上线！" % success_upline_number)
                    obj.redis_apply_status_update(statu=3)
                else:
                    self.message_user(request, "实例为 {0} 的实例上线失败，已存在上线实例，请检查".format(obj.redis_ins_name))
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
                obj = ApproveRedis(request, asset_id)
                deny_redis_ins = obj.deny_create()
                if deny_redis_ins:
                    deny_upline_number += 1
                    obj.redis_apply_status_update(statu=4)
                    self.message_user(request, "已拒绝  %s  个新Redis实例上线！" % deny_upline_number)
                else:
                    self.message_user(request, "操作实例为 {0} 的实例失败，已存在上线实例，请检查".format(obj.redis_ins_name))
        except ValueError as e:
            self.message_user(request, "操作实例为 {0} 的实例失败，原因为{1}".format(queryset, e))
    deny_selected_new_assets.short_description = "拒绝选择的Redis实例"


class RedisApprovalAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        """
        禁用添加按钮
        :param request:
        :return:
        """
        return False

    def has_delete_permission(self, request, obj=None):
        """
        禁用删除按钮
        :param request:
        :param obj:
        :return:
        """
        return False

    def get_actions(self, request):
        """
        在actions中去掉‘删除’操作
        :param request:
        :return:
        """
        actions = super(RedisApprovalAdmin, self).get_actions(request)
        if request.user.username[0].upper() != 'J':
            if 'delete_selected' in actions:
                del actions['delete_selected']
        return actions

    def get_queryset(self, request):
        """函数作用：使当前登录的用户只能看到自己负责的实例"""
        qs = super(RedisApprovalAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(create_user=RedisApply.objects.filter(create_user=request.user))

    # def ins_status_color(self, obj):
    #     ins_status = ''
    #     ins_choice = [
    #         (0, "已上线"),
    #         (1, "已下线"),
    #         (2, "未审批"),
    #         (3, "已审批"),
    #         (4, "已拒绝"),
    #     ]
    #     if obj.ins_status == 0:
    #         color = 'red'
    #         ins_status = ins_choice[obj.ins_status][1]
    #     elif obj.ins_status == 1:
    #         color = 'green'
    #         ins_status = ins_choice[obj.ins_status][1]
    #     elif obj.ins_status == 2:
    #         color = 'blue'
    #         ins_status = ins_choice[obj.ins_status][1]
    #     elif obj.ins_status == 3:
    #         color = 'green'
    #         ins_status = ins_choice[obj.ins_status][1]
    #     elif obj.ins_status == 4:
    #         color = 'blue'
    #         ins_status = ins_choice[obj.ins_status][1]
    #     else:
    #         color = ''
    #     return format_html(
    #         '<font size="5" face="arial" color="{0}">{1}</font>',
    #         color,
    #         ins_status,
    #     )
    # ins_status_color.short_description = u'实例状态'

    list_display = ['id', 'redis_ins_name', 'ins_disc', 'redis_type',
                    'redis_mem', 'sys_author', 'area',
                    'pub_date', 'approval_user', 'ins_status', 'on_line_status'
                    # 'show_all_ip', 'ins_status_color'
                    ]
    list_filter = ['redis_type']
    search_fields = ['area', 'ins_status']
    actions = ['apply_selected_new_redis', 'deny_selected_new_redis']
    inlines = [ChoiceInline]
    list_per_page = 15

    # 审核项有且只能有一条记录
    ChoiceInline.max_num = 1

    def return_message(self, request, queryset, mem=None):
        self.message_user(request, "操作实例为 {0} 的实例失败，原因为{1}".format(queryset, mem))


class RunningInsTimeAdmin(InlineActionsModelAdminMixin, admin.ModelAdmin):
    def has_add_permission(self, request):
        """
        禁用添加按钮
        :param request:
        :return:
        """
        return False

    def has_delete_permission(self, request, obj=None):
        """
        禁用删除按钮
        :param request:
        :param obj:
        :return:
        """
        return False

    def get_actions(self, request):
        """
        在actions中去掉‘删除’操作
        :param request:
        :return:
        """
        actions = super(RunningInsTimeAdmin, self).get_actions(request)
        if request.user.username[0].upper() != 'J':
            if 'delete_selected' in actions:
                del actions['delete_selected']
        return actions

    # def redis_qps(self, obj):
    #     button_html = """<a class="changelink" href="/polls/redis_qps/{0}/">QPS监控趋势图</a>""".format(obj.id)
    #     return format_html(button_html)
    # redis_qps.short_description = "QPS监控趋势图"
    #
    # def redis_stop(self, obj):
    #     button_html = """<a class="changelink" href="/polls/apis/redis-start/{0}/">启动</a>""".format(obj.id)
    #     return format_html(button_html)
    # redis_stop.short_description = "启动"
    #
    # def redis_start(self, obj):
    #     button_html = """<a class="changelink" href="/polls/apis/redis-stop/{0}/">停止</a>""".format(obj.id)
    #     return format_html(button_html)
    # redis_start.short_description = "停止"

    def get_form(self, request, obj=None, **args):
        """
        设置内联样式
        """
        defaults = {}
        if obj is not None:
            if obj.redis_type == 'Redis-Standalone':
                self.inlines = [RunningInsStandaloneInline]  # 设置内联
                RunningInsStandaloneInline.max_num = 1
            elif obj.redis_type == 'Redis-Sentinel':
                self.inlines = [RunningInsSentinelInline]
                RunningInsSentinelInline.max_num = len(RunningInsSentinel.objects.filter(running_ins_name=obj.running_ins_name))
        else:
            self.inlines = []  # 如果不是继承，就取消设置
        defaults.update(args)
        return super(RunningInsTimeAdmin, self).get_form(request, obj, **defaults)

    # def changelist_view(self, request, extra_context=None):
    #     self.list_display = ['id', 'running_ins_name', 'redis_type',
    #                     'redis_ip', 'running_ins_port', 'redis_ins_mem',
    #                     'redis_qps', 'redis_start', 'redis_stop']
    #     return super(RunningInsTimeAdmin, self).changelist_view(request, extra_context=None)

    list_display = ['id', 'running_ins_name', 'redis_type',
                    'command_hit_rate', 'running_time', 'redis_ins_mem',
                    # 'redis_qps', 'redis_start', 'redis_stop'
                    ]
    list_filter = ['running_ins_name']
    search_fields = ['redis_type']
    # inlines = [RealTimeQpsInline]
    RealTimeQpsInline.max_num = 15
    list_per_page = 15
    fieldsets = (
        ('Redis实例详情', {
            'fields': ('running_ins_name', 'redis_type', 'redis_ins_mem')
        }),
    )


class RealTimeQpsAdmin(admin.ModelAdmin):
    list_display = ['id', 'redis_running_monitor', 'collect_date', 'redis_used_mem', 'redis_qps', 'redis_ins_used_mem']
    list_filter = ['redis_running_monitor']
    search_fields = ['collect_date']
    list_per_page = 15


class RedisSentienlConfAdmin(admin.ModelAdmin):
    list_display = ['id', 'redis_type']


admin.site.register(LogEntry, LogEntryAdmin)
admin.site.register(Ipaddr, IpaddrAdmin)
# 申请
admin.site.register(ApplyRedisInfo, ApplyRedisInfoAdmin)
# 审批
admin.site.register(RedisApply, RedisApplyAdmin)
admin.site.register(RedisIns, RedisApprovalAdmin)
# admin.site.register(RedisVersion, RedisVersionAdmin)
admin.site.register(RedisConf, RedisConfAdmin)
# admin.site.register(RedisModel, RedisModelAdmin)
admin.site.register(RunningInsTime, RunningInsTimeAdmin)
admin.site.register(RealTimeQps, RealTimeQpsAdmin)
admin.site.register(RedisSentienlConf, RedisSentienlConfAdmin)
