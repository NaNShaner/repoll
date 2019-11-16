# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Create your models here.
from django.db import models
from django.utils import timezone
from django.utils.html import format_html
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
        verbose_name_plural = "资源池服务器列表"


class ApplyRedisInfo(models.Model):
    apply_ins_name = models.CharField(max_length=50, unique=True, verbose_name="应用名称")
    ins_disc = models.CharField(max_length=150, verbose_name="应用描述")
    type_choice = [
        ("Redis-Standalone", "Redis-Standalone"),
        ("Redis-Cluster", "Redis-Cluster"),
        ("Redis-Sentinel", "Redis-Sentinel")
    ]
    redis_type = models.CharField(max_length=60, default=type_choice[0][0], choices=type_choice, verbose_name="存储种类")
    redis_mem = models.CharField(max_length=50, help_text="例如填写：512M,1G,2G..32G等", verbose_name="内存总量")
    sys_author = models.CharField(max_length=50, verbose_name="项目负责人")
    area = models.CharField(max_length=50, verbose_name="机房")
    pub_date = models.DateTimeField('申请时间', default=timezone.now)
    user = User.objects.all()
    user_list = [u.__dict__['username'] for u in user]
    user_choice = zip(user_list, user_list)

    create_user = models.CharField(max_length=150, choices=user_choice, null=True, verbose_name="申请人", default="")
    status_choice = [
        (0, "已上线"),
        (1, "已下线"),
        (2, "未审批"),
        (3, "已审批"),
        (4, "已拒绝"),
        (5, "申请中"),
    ]
    apply_status = models.IntegerField(choices=status_choice, default=status_choice[5][0], blank=True, null=True,
                                       verbose_name="申请状态")

    class Meta:
        ordering = ('-pub_date', )
        verbose_name_plural = "Redis实例申请"

    def __str__(self):
        return self.apply_ins_name

    # def save(self, *args, **kwargs):
    #     a = args
    #     b = kwargs
    #     print(a,b)


class RedisInfo(models.Model):
    sys_type = models.CharField(max_length=5, unique=True)
    type_choice = [
        ("Redis-Standalone", "Redis-Standalone"),
        ("Redis-Cluster", "Redis-Cluster"),
        ("Redis-Sentinel", "Redis-Sentinel")
    ]
    redis_type = models.CharField(max_length=60, default=type_choice[0][0], choices=type_choice, verbose_name="存储种类")
    redis_port = models.IntegerField(verbose_name="Redis 端口", default=6379)
    pub_date = models.DateTimeField('date published')
    host_ip = models.ForeignKey(Ipaddr, on_delete=models.CASCADE)

    class Meta:
        ordering = ('-pub_date', )
        verbose_name_plural = "Redis实例信息"

    def __str__(self):
        return self.sys_type


class RedisApply(models.Model):
    apply_ins_name = models.CharField(max_length=50, verbose_name="应用名称")
    ins_disc = models.CharField(max_length=150, verbose_name="应用描述")
    type_choice = [
        ("Redis-Standalone", "Redis-Standalone"),
        ("Redis-Cluster", "Redis-Cluster"),
        ("Redis-Sentinel", "Redis-Sentinel")
    ]
    redis_type = models.CharField(max_length=60, default=type_choice[0][0], choices=type_choice, verbose_name="存储种类")
    redis_mem = models.CharField(max_length=50, help_text="例如填写：512M,1G,2G..32G等", verbose_name="内存总量")
    sys_author = models.CharField(max_length=50, verbose_name="项目负责人")
    area = models.CharField(max_length=50, verbose_name="机房")
    pub_date = models.DateTimeField('申请时间', default=timezone.now)
    create_user = models.CharField(max_length=150, null=True, verbose_name="申请人")
    status_choice = [
        (0, "已上线"),
        (1, "已下线"),
        (2, "未审批"),
        (3, "已审批"),
        (4, "已拒绝"),
        (5, "申请中"),
    ]
    apply_status = models.IntegerField(choices=status_choice, default=status_choice[5][0], blank=True, null=True,
                                       verbose_name="申请状态")

    class Meta:
        ordering = ('-pub_date', )
        verbose_name_plural = "Redis实例审批"

    def __str__(self):
        return self.apply_ins_name


class RedisIns(models.Model):
    redis_ins_name = models.CharField(max_length=50, null=True, verbose_name="应用名称")
    ins_disc = models.CharField(max_length=150, verbose_name="应用描述")
    type_choice = [
        ("Redis-Standalone", "Redis-Standalone"),
        ("Redis-Cluster", "Redis-Cluster"),
        ("Redis-Sentinel", "Redis-Sentinel")
    ]
    redis_version = models.CharField(max_length=150, null=True, verbose_name="Redis 版本", default="3.0.6")
    redis_type = models.CharField(max_length=60, default=type_choice[0][0], choices=type_choice, verbose_name="存储种类")
    redis_mem = models.CharField(max_length=50, help_text="例如填写：512M,1G,2G..32G等", verbose_name="内存总量")
    sys_author = models.CharField(max_length=50, verbose_name="项目负责人")
    area = models.CharField(max_length=50, verbose_name="机房")
    pub_date = models.DateTimeField('审批时间', default=timezone.now)
    approval_user = models.CharField(max_length=150, null=True, verbose_name="审批人")
    ins_choice = [
        (0, "已上线"),
        (1, "已下线"),
        (2, "未审批"),
        (3, "已审批"),
        (4, "已拒绝"),
    ]
    ins_status = models.IntegerField(choices=ins_choice, default=ins_choice[2][0], blank=True, verbose_name="实例状态")

    class Meta:
        ordering = ('-pub_date', )
        verbose_name = "Redis Approve"
        verbose_name_plural = "Redis上线配置"

    def __str__(self):
        return self.redis_ins_name

    def ins_status_color(self):
        if self.ins_status == 0:
            color = '#00F'
        elif self.ins_status == 1:
            color = '#F01'
        elif self.ins_status == 2:
            color = '#F02'
        elif self.ins_status == 3:
            color = '#F03'
        elif self.ins_status == 4:
            color = '#F04'
        else:
            color = ''
        return format_html(
            '<span style="color: {}">{}</span>',
            color,
            self.ins_status,
        )


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
        verbose_name_plural = "Redis模式视图"


class RedisConf(models.Model):
    redis_version = models.CharField(max_length=150, verbose_name="Redis版本", default="3.0.6")
    choice_list = [
        ('Redis-Standalone', 'Redis-Standalone'),
        ('Redis-Cluster', 'Redis-Cluster'),
        ('Redis-Sentinel', 'Redis-Sentinel')
    ]
    redis_type = models.CharField(max_length=150, choices=choice_list,
                                  default=choice_list[0][0], verbose_name="Redis运行模式")
    choice_list = [
        (0, '无效'),
        (1, "有效")
    ]
    daemonize = models.CharField(max_length=30, default="yes", verbose_name="daemonize")
    tcp_backlog = models.IntegerField(default=511, help_text="TCP连接完成队列", verbose_name="tcp-backlog")
    timeout = models.IntegerField(default=0, help_text="客户端闲置多少秒后关闭连接,默认为0,永不关闭", verbose_name="timeout")
    tcp_keepalive = models.IntegerField(default=60, help_text="检测客户端是否健康周期,默认关闭", verbose_name="tcp-keepalive")
    loglevel = models.CharField(max_length=50, default="notice", help_text="日志级别", verbose_name="loglevel")
    databases = models.IntegerField(help_text="可用的数据库数，默认值为16个,默认数据库为0", verbose_name="databases", default=16)
    dir = models.CharField(max_length=150, help_text="redis工作目录", verbose_name="dir", default="/opt/repoll/")
    stop_writes_on_bgsave_error = models.CharField(max_length=150, help_text="bgsave出错了不停写",
                                                   verbose_name="stop-writes-on-bgsave-error", default="no")
    repl_timeout = models.IntegerField(help_text="master批量数据传输时间或者ping回复时间间隔,默认:60秒",
                                       verbose_name="repl-timeout", default="60")
    repl_ping_slave_period = models.IntegerField(help_text="指定slave定期ping master的周期,默认:10秒",
                                                 verbose_name="repl-ping-slave-period", default=10)
    repl_disable_tcp_nodelay = models.CharField(max_length=150, help_text="是否禁用socket的NO_DELAY,默认关闭，影响主从延迟",
                                                verbose_name="repl-disable-tcp-nodelay", default="no")
    repl_backlog_size = models.CharField(max_length=150, help_text="复制缓存区,默认:1mb,配置为:10Mb",
                                         verbose_name="repl-backlog-size", default="10M")
    repl_backlog_ttl = models.IntegerField(help_text="master在没有Slave的情况下释放BACKLOG的时间多久:默认:3600,配置为:7200", verbose_name="repl-backlog-ttl", default=7200)
    slave_serve_stale_data = models.CharField(max_length=150,
                                              help_text="当slave服务器和master服务器失去连接后，或者当数据正在复制传输的时候，"
                                                        "如果此参数值设置“yes”，slave服务器可以继续接受客户端的请求",
                                              verbose_name="slave-serve-stale-data", default="yes")
    slave_read_only = models.CharField(max_length=150,
                                       help_text="slave服务器节点是否只读,cluster的slave节点默认读写都不可用,需要调用readonly开启可读模式",
                                       verbose_name="slave-read-only", default="yes")
    slave_priority = models.IntegerField(help_text="slave的优先级,影响sentinel/cluster晋升master操作,0永远不晋升",
                                         verbose_name="slave-priority", default=100)
    lua_time_limit = models.IntegerField(help_text="Lua脚本最长的执行时间，单位为毫秒", verbose_name="lua-time-limit", default=5000)
    slowlog_log_slower_than = models.IntegerField(help_text="慢查询被记录的阀值,默认10毫秒", verbose_name="slowlog-log-slower-than", default=10000)
    slowlog_max_len = models.IntegerField(help_text="最多记录慢查询的条数", verbose_name="slowlog-max-len", default=128)
    hash_max_ziplist_entries = models.IntegerField(help_text="hash数据结构优化参数",
                                                   verbose_name="hash-max-ziplist-entries", default=512)
    hash_max_ziplist_value = models.IntegerField(help_text="hash数据结构优化参数",
                                                 verbose_name="hash-max-ziplist-value", default=64)
    list_max_ziplist_entries = models.IntegerField(help_text="list数据结构优化参数",
                                                   verbose_name="list-max-ziplist-entries", default=512)
    list_max_ziplist_value = models.IntegerField(help_text="list数据结构优化参数",
                                                 verbose_name="list-max-ziplist-value", default=64)
    set_max_intset_entries = models.IntegerField(help_text="set数据结构优化参数",
                                                 verbose_name="set-max-intset-entriesr", default=512)
    zset_max_ziplist_entries = models.IntegerField(help_text="zset数据结构优化参数",
                                                   verbose_name="zset-max-ziplist-entries", default=128)
    zset_max_ziplist_value = models.IntegerField(help_text="zset数据结构优化参数",
                                                 verbose_name="zset-max-ziplist-value", default=64)
    activerehashing = models.CharField(max_length=150, help_text="是否激活重置哈希,默认:yes",
                                       verbose_name="activerehashing", default="yes")
    clientOutputBufferLimitNormal = models.CharField(max_length=150, help_text="客户端输出缓冲区限制(客户端)",
                                                          verbose_name="client-output-buffer-limit normal", default="0 0 0")
    clientOutputBufferLimitSlave = models.CharField(max_length=150, help_text="客户端输出缓冲区限制(复制)",
                                                         verbose_name="client-output-buffer-limit slave", default="512mb 128mb 60")
    clientOutputBufferLimitPubsub = models.CharField(max_length=150, help_text="客户端输出缓冲区限制(发布订阅)",
                                                          verbose_name="client-output-buffer-limit pubsub", default="32mb 8mb 60")
    hz = models.IntegerField(help_text="执行后台task数量,默认:10", verbose_name="hz", default=10)
    port = models.CharField(max_length=150, help_text="端口", verbose_name="port", default="%port%")
    maxmemory = models.CharField(max_length=150, help_text="当前实例最大可用内存", verbose_name="maxmemory", default="%dmb%")
    maxmemory_policy = models.CharField(max_length=150, help_text="内存不够时,淘汰策略,默认:volatile-lru",
                                        verbose_name="maxmemory-policy", default="volatile-lru")
    appendonly = models.CharField(max_length=150, help_text="开启append only持久化模式",
                                  verbose_name="appendonly", default="yes")
    appendfsync = models.CharField(max_length=150, help_text="默认:aof每秒同步一次",
                                   verbose_name="appendfsync", default="everysec")
    appendfilename = models.CharField(max_length=150, help_text="aof文件名称,默认:appendonly-{port}.aof",
                                      verbose_name="appendfilename", default="appendonly-%port%.aof")
    dbfilename = models.CharField(max_length=150, help_text="RDB文件默认名称,默认dump-{port}.rdb",
                                  verbose_name="dbfilename", default="dump-%port%.rdb")
    aof_rewrite_incremental_fsync = models.CharField(max_length=150,
                                                     help_text="aof rewrite过程中,是否采取增量文件同步策略,默认:yes",
                                                     verbose_name="aof-rewrite-incremental-fsync", default="yes")
    no_appendfsync_on_rewrite = models.CharField(max_length=150,
                                                 help_text="是否在后台aof文件rewrite期间调用fsync,默认调用,修改为yes,防止可能fsync阻塞,但可能丢失rewrite期间的数据",
                                                 verbose_name="no-appendfsync-on-rewrite", default="yes")
    auto_aof_rewrite_min_size = models.CharField(max_length=150, help_text="触发rewrite的aof文件最小阀值,默认64m",
                                                 verbose_name="auto-aof-rewrite-min-size", default="64m")
    auto_aof_rewrite_percentage = models.CharField(max_length=150, help_text="Redis重写aof文件的比例条件,默认从100开始,统一机器下不同实例按4%递减",
                                                   verbose_name="auto-aof-rewrite-percentage", default="%d")
    rdbcompression = models.CharField(max_length=150, help_text="rdb是否压缩", verbose_name="rdbcompression", default="yes")
    rdbchecksum = models.CharField(max_length=150, help_text="rdb校验和", verbose_name="rdbchecksum", default="yes")
    repl_diskless_sync = models.CharField(max_length=150, help_text="开启无盘复制", verbose_name="repl-diskless-sync", default="no")
    repl_diskless_sync_delay = models.IntegerField(help_text="无盘复制延时", verbose_name="repl-diskless-sync-delay", default=5)
    save900 = models.IntegerField(help_text="900秒有一次修改做bgsave", verbose_name="save 900", default=1)
    save300 = models.IntegerField(help_text="rdb校验和", verbose_name="save 300", default=10)
    save60 = models.IntegerField(help_text="60秒有10000次修改做bgsave", verbose_name="save 60", default=10000)
    maxclients = models.IntegerField(help_text="客户端最大连接数", verbose_name="maxclients", default=10000)
    hll_sparse_max_bytes = models.IntegerField(help_text="HyperLogLog稀疏表示限制设置", verbose_name="hll-sparse-max-bytes", default=3000)
    min_slaves_to_write = models.IntegerField(help_text="当slave数量小于min-slaves-to-write，且延迟小于等于min-slaves-max-lag时， master停止写入操作",
                                              verbose_name="min-slaves-to-write", default=0)
    min_slaves_max_lag = models.IntegerField(help_text="当slave服务器和master服务器失去连接后，或者当数据正在复制传输的时候，如果此参数值设置yes，slave服务器可以继续接受客户端的请求",
                                             verbose_name="min-slaves-max-lag", default=10)
    aof_load_truncated = models.CharField(max_length=150, help_text="客户端最大连接数", verbose_name="aof-load-truncated", default="yes")
    notify_keyspace_events = models.CharField(max_length=150, help_text="keyspace事件通知功能", blank=True,
                                              verbose_name="notify-keyspace-events", null=True, default="")
    logfile = models.CharField(max_length=150, help_text="Redis日志存放路径",
                               verbose_name="logfile", default="/opt/repoll/")

    def __str__(self):
        # return self.redis_version
        return self.redis_version

    class Meta:
        verbose_name_plural = "Redis配置信息"


class RedisSentienlConf(models.Model):
    port = models.CharField(max_length=150, help_text="sentinel实例端口", verbose_name="port", default="%port%")
    dir = models.CharField(max_length=150, help_text="工作目录", verbose_name="dir", default="/opt/repoll/")
    sentinel_monitor = models.CharField(max_length=150,
                                        help_text="master名称定义和最少参与监控的sentinel数,格式:masterName ip port num",
                                        verbose_name="sentinel monitor",
                                        default="%masterName_ip_port_num%")
    sentinel_down_after_milliseconds = models.CharField(max_length=150,
                                                        help_text="Sentinel判定服务器断线的毫秒数",
                                                        verbose_name="sentinel down-after-milliseconds",
                                                        default="%s 20000%")
    sentinel_failover_timeout = models.CharField(max_length=150,
                                                 help_text="故障迁移超时时间,默认:3分钟",
                                                 verbose_name="sentinel failover-timeout",
                                                 default="%s 180000%")
    sentinel_parallel_syncs = models.CharField(max_length=150,
                                               help_text="在执行故障转移时,最多有多少个从服务器同时对新的主服务器进行同步,默认:1",
                                               verbose_name="sentinel parallel-syncs",
                                               default="%s 1%")

    def __str__(self):
        return "Sentinel 配置成功"

    class Meta:
        verbose_name_plural = "Redis Sentinel配置信息"


class RedisVersion(models.Model):
    redis_version = models.ForeignKey(RedisConf, on_delete=models.CASCADE)
    choice_list = [
        ('Redis-Standalone', 'Redis-Standalone'),
        ('Redis-Cluster', 'Redis-Cluster'),
        ('Redis-Sentinel', 'Redis-Sentinel')
    ]
    redis_type = models.CharField(max_length=150, choices=choice_list,
                                  default=choice_list[0][0], verbose_name="Redis运行模式")
    # redis_version = models.CharField(max_length=60, unique=True, primary_key=True,
    #                                  default="3.0.6", verbose_name="Redis版本", error_messages={'required': "不能为空"})
    pub_date = models.DateTimeField(default=timezone.now, verbose_name="版本发布时间")
    who_apply = models.CharField(max_length=60, default=User, verbose_name="版本发布人")

    def __str__(self):
        return "Redis版本添加成功"

    class Meta:
        ordering = ('-pub_date', )
        verbose_name = "RedisVersion"
        verbose_name_plural = "Redis版本视图"


class ApplyRedisText(models.Model):
    # ipaddr = models.ForeignKey(Ipaddr, on_delete=models.CASCADE, null=True)
    redis_ins = models.ForeignKey(RedisIns, on_delete=models.CASCADE)
    apply_text = models.TextField(max_length=250, verbose_name="实例详情",
                                  blank=True, null=True, help_text="具体规则如下: </br>"
                                                                   "1. standalone类型：</br>"
                                                                   "masterIp:masterPort:memSize(M)(例如：10.10.xx.xx:2048)</br>"
                                                                   "2. sentinel类型：</br>"
                                                                   "masterIp:masterPort:memSize(M):masterName:slaveIp:slavePort</br>"
                                                                   "sentinelIp1</br>"
                                                                   "sentinelIp2</br>"
                                                                   "sentinelIp3")
    who_apply_ins = models.CharField(max_length=50, default=User, verbose_name="审批人")
    apply_time = models.DateTimeField(verbose_name="审批时间", default=timezone.now)

    def __str__(self):
        # return self.redis_ins
        return "{0}".format("执行成功")

    class Meta:
        verbose_name_plural = "实例审批"


class RunningInsTime(models.Model):
    running_ins_name = models.CharField(max_length=50, null=True, unique=True, verbose_name="应用名称")
    choice_list = [
        ('Redis-Standalone', 'Redis-Standalone'),
        ('Redis-Cluster', 'Redis-Cluster'),
        ('Redis-Sentinel', 'Redis-Sentinel')
    ]
    redis_type = models.CharField(max_length=150, choices=choice_list,
                                  default=choice_list[0][0], verbose_name="Redis运行模式")
    running_ins_port = models.IntegerField(null=True, unique=True, verbose_name="端口")
    redis_ip = models.GenericIPAddressField(null=True, verbose_name="Redis IP地址")
    redis_ins_mem = models.CharField(max_length=50, null=True, verbose_name="实例内存")

    def __str__(self):
        return self.running_ins_name

    class Meta:
        verbose_name = "Redis Running Ins"
        verbose_name_plural = "Redis已运行实例"


class RealTimeQps(models.Model):
    redis_used_mem = models.CharField(default=0, null=True, max_length=50, verbose_name="Redis已用内存")
    collect_date = models.DateTimeField(auto_now=True, verbose_name="收集时间")
    redis_qps = models.FloatField(default=0, null=True, verbose_name="Redis QPS")
    redis_ins_used_mem = models.CharField(max_length=50, null=True, verbose_name="Redis内存使用率")
    redis_running_monitor = models.ForeignKey(RunningInsTime, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Redis Monitor"
        verbose_name_plural = "Redis监控信息"





