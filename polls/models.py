# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Create your models here.
from django.db import models
from django.utils import timezone
from django.utils.html import format_html
from .tools import redis_apply_text
from django.contrib.auth.models import User


class Ipaddr(models.Model):
    """
    服务器资源池列表
    TODO：服务器OS监控未添加
    """
    ip = models.GenericIPAddressField(verbose_name="服务器IP", unique=True, help_text="服务器IP地址")
    area = models.CharField(max_length=50, verbose_name="机房", help_text="机房区域")
    choice_list = [
        (0, '虚拟机'),
        (1, "物理机")
    ]
    machina_type = models.IntegerField(choices=choice_list, verbose_name="机器类型")
    machina_mem = models.CharField(max_length=50, verbose_name="内存大小", help_text="服务器内存大小")
    used_mem = models.CharField(max_length=50, null=True, verbose_name="已分配内存")
    used_cpu = models.CharField(max_length=50, null=True, verbose_name="CPU使用率")

    def __str__(self):
        return self.ip

    class Meta:
        verbose_name_plural = "资源池服务器列表"


class ServerUserPass(models.Model):
    """服务器用户名密码，平台用来远程管理"""
    user_name = models.CharField(default="repoll", max_length=50, verbose_name="服务器用户名", help_text="服务器用户名")
    user_passwd = models.CharField(default="", max_length=128, verbose_name="服务器用户密码", help_text="服务器用户密码")
    server_ip = models.ForeignKey(Ipaddr, to_field="ip", on_delete=models.CASCADE)

    def __str__(self):
        return self.user_name

    class Meta:
        verbose_name_plural = "服务器资源池用户配置"


class ApplyRedisInfo(models.Model):
    """记录Redis实例申请详情"""
    apply_ins_name = models.CharField(max_length=50, unique=True, verbose_name="应用名称")
    ins_disc = models.CharField(max_length=150, verbose_name="应用描述")
    type_choice = [
        ("Redis-Standalone", "Redis-Standalone"),
        ("Redis-Cluster", "Redis-Cluster"),
        ("Redis-Sentinel", "Redis-Sentinel")
    ]
    redis_type = models.CharField(max_length=60, default=type_choice[0][0], choices=type_choice, verbose_name="存储种类")
    redis_mem = models.CharField(max_length=50, help_text="例如填写：512M,1G,2G..32G等", verbose_name="内存总量")
    # sys_author = models.CharField(max_length=50, verbose_name="项目负责人")
    sys_author = models.ForeignKey(User, on_delete=models.CASCADE, to_field="username",
                                   related_name="apply_redis_info_sys_author", verbose_name="项目负责人")
    area = models.CharField(max_length=50, verbose_name="机房")
    pub_date = models.DateTimeField('申请时间', default=timezone.now)
    # user = User.objects.all()
    # user_list = [u.__dict__['username'] for u in user]
    # user_choice = zip(user_list, user_list)
    create_user = models.CharField(max_length=150, null=True, verbose_name="申请人", default="")
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
    """用于管理员审批已申请的redis实例"""
    apply_ins_name = models.CharField(max_length=50, verbose_name="应用名称")
    ins_disc = models.CharField(max_length=150, verbose_name="应用描述")
    type_choice = [
        ("Redis-Standalone", "Redis-Standalone"),
        ("Redis-Cluster", "Redis-Cluster"),
        ("Redis-Sentinel", "Redis-Sentinel")
    ]
    redis_type = models.CharField(max_length=60, default=type_choice[0][0], choices=type_choice, verbose_name="存储种类")
    redis_mem = models.CharField(max_length=50, help_text="例如填写：512M,1G,2G..32G等", verbose_name="内存总量")
    # sys_author = models.CharField(max_length=50, verbose_name="项目负责人")
    sys_author = models.ForeignKey(User, on_delete=models.CASCADE, default="", to_field="username",
                                   related_name="ins_sys_author", verbose_name="项目负责人")
    area = models.CharField(max_length=50, verbose_name="机房")
    pub_date = models.DateTimeField('申请时间', default=timezone.now)
    # create_user = models.CharField(max_length=150, null=True, verbose_name="申请人")
    create_user = models.ForeignKey(User, on_delete=models.CASCADE, default="", to_field="username",
                                    related_name="create_user", verbose_name="申请人")
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
    """用于DBA对已通过审批的redis实例进行配置上线"""
    redis_ins_name = models.CharField(max_length=50, unique=True, null=True, verbose_name="应用名称")
    ins_disc = models.CharField(max_length=150, verbose_name="应用描述")
    type_choice = [
        ("Redis-Standalone", "Redis-Standalone"),
        ("Redis-Cluster", "Redis-Cluster"),
        ("Redis-Sentinel", "Redis-Sentinel")
    ]
    redis_version = models.CharField(max_length=150, null=True, verbose_name="Redis 版本", default="3.0.6")
    redis_type = models.CharField(max_length=60, default=type_choice[0][0], choices=type_choice, verbose_name="存储种类")
    redis_mem = models.CharField(max_length=50, help_text="例如填写：512M,1G,2G..32G等", verbose_name="内存总量")
    # sys_author = models.CharField(max_length=50, verbose_name="项目负责人")
    sys_author = models.ForeignKey(User, on_delete=models.CASCADE, default="", to_field="username",
                                   related_name="redis_ins_sys_author", verbose_name="项目负责人")
    area = models.CharField(max_length=50, verbose_name="机房")
    pub_date = models.DateTimeField('审批时间', default=timezone.now)
    # approval_user = models.CharField(max_length=150, null=True, verbose_name="审批人")
    approval_user = models.ForeignKey(User, on_delete=models.CASCADE, default="", to_field="username",
                                      verbose_name="审批人")
    ins_choice = [
        (0, "已上线"),
        (1, "已下线"),
        (2, "未审批"),
        (3, "已审批"),
        (4, "已拒绝"),
    ]
    ins_status = models.IntegerField(choices=ins_choice, default=ins_choice[2][0], blank=True, verbose_name="实例状态")
    on_line_status_choice = [
        (0, "已上线"),
        (1, "已下线"),
        (2, "未上线"),
    ]
    on_line_status = models.IntegerField(choices=on_line_status_choice, default=on_line_status_choice[2][0], blank=True, verbose_name="上线状态")

    class Meta:
        ordering = ('-pub_date', )
        verbose_name = "Redis Ins"
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
    """暂未使用"""
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
    """管理Redis的配置信息"""
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
                                                   verbose_name="auto-aof-rewrite-percentage", default="100")
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
    aof_load_truncated = models.CharField(max_length=150, help_text="指redis在恢复时，会忽略最后一条可能存在问题的指令", verbose_name="aof-load-truncated", default="yes")
    notify_keyspace_events = models.CharField(max_length=150, help_text="keyspace事件通知功能", blank=True,
                                              verbose_name="notify-keyspace-events", null=True, default="")
    logfile = models.CharField(max_length=150, help_text="Redis日志存放路径",
                               verbose_name="logfile", default="/opt/repoll/")

    # 默认Redis密码
    masterauth = models.CharField(max_length=150, help_text="当master服务设置了密码保护时slave服务连接master的密码",
                                  verbose_name="masterauth", null=True, blank=True, default="qZr3pet")
    requirepass = models.CharField(max_length=150, help_text="设置客户端连接后进行任何其他指定前需要使用的密码",
                                   verbose_name="requirepass", null=True, blank=True, default="qZr3pet")

    def __str__(self):
        return self.redis_version

    class Meta:
        verbose_name_plural = "Redis Standalone配置信息"


class RedisSentienlConf(models.Model):
    """管理哨兵配置信息"""
    choice_list = [
        ('Redis-Sentinel', 'Redis-Sentinel')
    ]
    redis_type = models.CharField(max_length=150, choices=choice_list,
                                  default=choice_list[0][0], verbose_name="Redis运行模式")
    daemonize = models.CharField(max_length=30, default="yes", verbose_name="daemonize")
    port = models.CharField(max_length=150, help_text="sentinel实例端口", verbose_name="port", default="%port%")
    dir = models.CharField(max_length=150, help_text="工作目录", verbose_name="dir", default="/opt/repoll/")
    sentinelMonitor = models.CharField(max_length=150,
                                       help_text="master名称定义和最少参与监控的sentinel数,格式:masterName ip port num",
                                       verbose_name="sentinel monitor",
                                       default="%masterName_ip_port_num%")
    sentinelDownAfterMilliseconds = models.CharField(max_length=150,
                                                     help_text="Sentinel判定服务器断线的毫秒数",
                                                     verbose_name="sentinel down-after-milliseconds",
                                                     default="%s 20000%")
    sentinelFailoverTimeout = models.CharField(max_length=150,
                                               help_text="故障迁移超时时间,默认:3分钟",
                                               verbose_name="sentinel failover-timeout",
                                               default="%s 180000%")
    sentinelParallelSyncs = models.CharField(max_length=150,
                                             help_text="在执行故障转移时,最多有多少个从服务器同时对新的主服务器进行同步,默认:1",
                                             verbose_name="sentinel parallel-syncs",
                                             default="%s 1%")
    logfile = models.CharField(max_length=150, help_text="Redis日志存放路径",
                               verbose_name="logfile", default="/opt/repoll/")
    # 默认Redis密码
    authPass = models.CharField(max_length=150, help_text="当master服务设置了密码保护时slave服务连接master的密码",
                                verbose_name="auth-pass", null=True, blank=True, default="qZr3pet")

    def __str__(self):
        return "Sentinel 配置成功"

    class Meta:
        verbose_name_plural = "Redis Sentinel配置信息"


class RedisClusterConf(models.Model):
    """管理集群配置信息"""
    choice_list = [
        ('Redis-Cluster', 'Redis-Cluster')
    ]
    redis_type = models.CharField(max_length=150, choices=choice_list,
                                  default=choice_list[0][0], verbose_name="Redis运行模式")
    cluster_enabled = models.CharField(max_length=150, default="yes",
                                       verbose_name="cluster-enabled",
                                       help_text="是否开启集群模式")
    cluster_node_timeout = models.IntegerField(default=15000,
                                               verbose_name="cluster-slave-validity-factor",
                                               help_text="集群节点超时时间,默认15秒")
    cluster_slave_validity_factor = models.IntegerField(default=10,
                                                        help_text="从节点延迟有效性判断因子,默认10秒",
                                                        verbose_name="cluster-slave-validity-factor")
    cluster_migration_barrier = models.IntegerField(default=1,
                                                    help_text="主从迁移至少需要的从节点数,默认1个",
                                                    verbose_name="cluster-migration-barrier")
    clusterconfigfile = models.CharField(max_length=150,
                                         help_text="集群配置文件名称,格式:nodes-{port}.conf",
                                         verbose_name="cluster-config-file",
                                         default="nodes-%d.conf")
    cluster_require_full_coverage = models.CharField(max_length=150,
                                                     help_text="节点部分失败期间,其他节点是否继续工作",
                                                     verbose_name="sentinel down-after-milliseconds",
                                                     default="no")

    def __str__(self):
        return "Cluster 配置成功"

    class Meta:
        verbose_name_plural = "Redis Cluster配置信息"


class RedisVersion(models.Model):
    """暂未使用"""
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
    # who_apply = models.CharField(max_length=60, default="", verbose_name="版本发布人")
    who_apply = models.ForeignKey(User, on_delete=models.CASCADE, default="", to_field="username",
                                  related_name="who_apply", verbose_name="版本发布人")

    def __str__(self):
        return "Redis版本添加成功"

    class Meta:
        ordering = ('-pub_date', )
        verbose_name = "RedisVersion"
        verbose_name_plural = "Redis版本视图"


class ApplyRedisText(models.Model):
    """用于DBA配置已审批通过的Redis实例"""
    # ipaddr = models.ForeignKey(Ipaddr, on_delete=models.CASCADE, null=True)
    redis_ins = models.ForeignKey(RedisIns, to_field="redis_ins_name", on_delete=models.CASCADE)
    apply_text = models.TextField(max_length=2400, verbose_name="实例详情",
                                  blank=True, null=True, help_text="具体规则如下: </br>"
                                                                   "1. standalone类型：</br>"
                                                                   "masterIp:masterPort:memSize(M)(例如：10.10.xx.xx:2048)</br>"
                                                                   "2. sentinel类型：</br>"
                                                                   "masterIp:masterPort:memSize(M):masterName:slaveIp:slavePort</br>"
                                                                   "sentinelIp1:sentinelPort1</br>"
                                                                   "sentinelIp2:sentinelPort2</br>"
                                                                   "sentinelIp3:sentinelPort3</br>"
                                                                   "3. Cluster类型:（集群各实例端口不建议大于50000）</br>"
                                                                   "master1Ip:master1Port:memSize(M):slave1Ip:slave1Port</br>" 
                                                                   "master2Ip:master2Port:memSize(M):slave2Ip:slave2Port</br>" 
                                                                   "master3Ip:master3Port:memSize(M):slave3Ip:slave3Port</br>",
                                  error_messages={'required': "不能为空"},
                                  validators=[redis_apply_text])
    # who_apply_ins = models.CharField(max_length=50, default="", verbose_name="审批人")
    who_apply_ins = models.ForeignKey(User, on_delete=models.CASCADE, default="",
                                      related_name="who_apply_ins", to_field="username", verbose_name="审批人")
    apply_time = models.DateTimeField(verbose_name="审批时间", default=timezone.now)

    def __str__(self):
        return "{0}".format("执行成功")

    class Meta:
        verbose_name_plural = "实例审批"


class RunningInsTime(models.Model):
    """用于记录DBA配置上线后的实例实际运行情况"""
    running_ins_name = models.CharField(max_length=50, unique=True, null=True, verbose_name="应用名称")
    choice_list = [
        ('Redis-Standalone', 'Redis-Standalone'),
        ('Redis-Cluster', 'Redis-Cluster'),
        ('Redis-Sentinel', 'Redis-Sentinel')
    ]
    redis_type = models.CharField(max_length=150, choices=choice_list,
                                  default=choice_list[0][0], verbose_name="Redis运行模式")
    redis_ins_mem = models.CharField(max_length=50, null=True, verbose_name="实例内存")
    running_ins_used_mem_rate = models.CharField(default="0", max_length=50, null=True, verbose_name="内存使用率")
    running_time = models.IntegerField(default=0, null=True, verbose_name="运行时间")
    running_type = models.CharField(max_length=50, default="未运行", null=True, verbose_name="运行状态")
    ins_choice = [
        (0, "已上线"),
        (1, "已下线"),
        (2, "未审批"),
        (3, "已审批"),
        (4, "已拒绝"),
    ]
    ins_status = models.IntegerField(choices=ins_choice, default=ins_choice[2][0],
                                     null=True, blank=True, verbose_name="实例状态")

    def __str__(self):
        return self.running_ins_name

    class Meta:
        verbose_name = "Redis Running Ins"
        verbose_name_plural = "Redis已运行实例"


class RunningInsStandalone(models.Model):
    """Standalone实例运行情况"""
    running_ins_name = models.CharField(max_length=50, null=True, verbose_name="应用名称")
    choice_list = [
        ('Redis-Standalone', 'Redis-Standalone'),
        ('Redis-Cluster', 'Redis-Cluster'),
        ('Redis-Sentinel', 'Redis-Sentinel')
    ]
    redis_type = models.CharField(max_length=150, choices=choice_list,
                                  default=choice_list[0][0], verbose_name="Redis运行模式")
    running_ins_port = models.IntegerField(default=6379, verbose_name="端口")
    redis_ip = models.GenericIPAddressField(default="", verbose_name="Redis IP地址")
    redis_ins_mem = models.CharField(max_length=50, null=True, verbose_name="实例内存")
    running_ins = models.ForeignKey(RunningInsTime, default="", on_delete=models.CASCADE)
    redis_ins_alive = models.CharField(default="未启动", max_length=50, null=True, verbose_name="实例存活状态")
    local_redis_config_file = models.CharField(default="", max_length=50, null=True, verbose_name="服务端配置文件存放路径")

    def __str__(self):
        return ""

    class Meta:
        verbose_name = "Redis Running Standalone Ins"
        verbose_name_plural = "运行实例详情"
        unique_together = ["redis_ip", "running_ins_port"]


class RunningInsSentinel(models.Model):
    """Sentinel运行情况"""
    running_ins_name = models.CharField(max_length=50, null=True, verbose_name="应用名称")
    choice_list = [
        ('Redis-Standalone', 'Redis-Standalone'),
        ('Redis-Cluster', 'Redis-Cluster'),
        ('Redis-Sentinel', 'Redis-Sentinel'),
        ('Redis-Master', 'Redis-Master'),
        ('Redis-Slave', 'Redis-Slave')
    ]
    redis_type = models.CharField(max_length=150, choices=choice_list,
                                  default=choice_list[0][0], verbose_name="Redis运行模式")
    running_ins_port = models.IntegerField(default=6379, verbose_name="端口")
    redis_ip = models.GenericIPAddressField(default="", verbose_name="Redis IP地址")
    redis_ins_mem = models.CharField(max_length=50, null=True, default="无", verbose_name="实例内存")
    running_ins_standalone = models.ForeignKey(RunningInsTime, unique=False, on_delete=models.CASCADE, null=True)
    redis_ins_alive = models.CharField(default="未启动", max_length=50, null=True, verbose_name="实例存活状态")
    local_redis_config_file = models.CharField(default="", max_length=50, null=True, verbose_name="服务端配置文件存放路径")

    def __str__(self):
        return ""

    class Meta:
        verbose_name = "Redis Running Sentinel Ins"
        verbose_name_plural = "运行实例详情"
        unique_together = ["redis_ip", "running_ins_port"]


class RunningInsCluster(models.Model):
    """Cluster运行情况"""
    running_ins_name = models.CharField(max_length=50, null=True, verbose_name="应用名称")
    choice_list = [
        ('Redis-Master', 'Redis-Master'),
        ('Redis-Slave', 'Redis-Slave')
    ]
    redis_type = models.CharField(max_length=150, choices=choice_list,
                                  default=choice_list[0][0], verbose_name="Redis运行模式")
    # running_ins_port = models.IntegerField(null=True, unique=True, verbose_name="端口")
    running_ins_port = models.IntegerField(default=6379, verbose_name="端口")
    redis_ip = models.GenericIPAddressField(default="", verbose_name="Redis IP地址")
    redis_ins_mem = models.CharField(max_length=50, null=True, default="无", verbose_name="实例内存")
    running_ins_standalone = models.ForeignKey(RunningInsTime, unique=False, on_delete=models.CASCADE, null=True)
    redis_ins_alive = models.CharField(default="未启动", max_length=50, null=True, verbose_name="实例存活状态")
    local_redis_config_file = models.CharField(default="", max_length=50, null=True, verbose_name="服务端配置文件存放路径")

    def __str__(self):
        return ""

    class Meta:
        verbose_name = "Redis Running Cluster Ins"
        verbose_name_plural = "运行实例详情"
        unique_together = ["redis_ip", "running_ins_port"]


class RealTimeQps(models.Model):
    """已运行实例的监控信息"""
    redis_used_mem = models.CharField(default=0, null=True, max_length=50, verbose_name="Redis已用内存")
    collect_date = models.DateTimeField(auto_now=True, verbose_name="收集时间")
    redis_qps = models.FloatField(default=0, null=True, verbose_name="Redis QPS")
    redis_ins_used_mem = models.CharField(max_length=50, null=True, verbose_name="Redis内存使用率")
    redis_running_monitor = models.ForeignKey(RunningInsTime, on_delete=models.CASCADE)
    redis_ip = models.GenericIPAddressField(default="", verbose_name="redis_ip", null=False)
    redis_port = models.IntegerField(default=0, verbose_name="redis_port", null=False)
    running_type = models.CharField(max_length=50, default="未运行", null=True, verbose_name="运行状态")

    class Meta:
        verbose_name = "Redis Monitor"
        verbose_name_plural = "Redis监控信息"
        index_together = ["redis_ip", "redis_port"]
