import time
import redis
from polls.models import RunningInsTime, RunningInsSentinel, RunningInsStandalone, RunningInsCluster, RealTimeQps
from django.utils import timezone
from polls.scheduled import RedisScheduled
import threading
import logging

# 日志格式
logger = logging.getLogger("redis.monitor")
# 常量定义，表示各类redis的运作模式
sentinel = "Redis-Sentinel"
standalone = 'Redis-Standalone'
cluster = "Redis-Cluster"
redis_err_type = "default"


def get_redis_status(func, ins_name, redis_ip, redis_port):
    """
    获取当前redis实例或集群的状态，判断是否需要执行入库操作
    :param func: RunningInsCluster(models.Model)
    :param ins_name:
    :param redis_ip:
    :param redis_port:
    :return:
    """
    running_type_dict = {}
    try:
        running_type = func.objects.filter(running_ins_name=ins_name).filter(redis_ip=redis_ip).filter(
            running_ins_port=redis_port).values("redis_ins_alive")
        running_type_dict = running_type.first()
    except Exception as e:
        logger.error(
            f"get_redis_status--end:{e}")
    logger.error(
        f"running_type:{running_type_dict}")
    return running_type_dict["redis_ins_alive"]


def set_redis_status(func, ins_name, mes, redis_ip, redis_port):
    """
    获取当前redis实例或集群的状态，判断是否需要执行入库操作
    :param func:
    :param ins_name:
    :param mes:
    :param redis_ip
    :param redis_port
    :return:
    """
    try:
        func.objects.filter(running_ins_name=ins_name).filter(redis_ip=redis_ip).filter(
            running_ins_port=redis_port).update(redis_ins_alive=mes)
    except ImportError as e:
        logger.error(e)
    return True


class AllRedisIns:
    def __init__(self, redis_name, redis_ins):
        """

        :param redis_name: 实例名称
        :param redis_ins:  实例对象obj
        :return:
        """
        # self.ip_port_dict = ip_port_dict
        self.sentinel = sentinel
        self.standalone = standalone
        self.cluster = cluster
        self.redis_err_type = redis_err_type
        # 平台内所有入库的redis 实例的ip地址和端口存入该列表
        self.all_ip_port = []
        # 平台内所有哨兵实例的ip地址和端口存入该列表
        self.all_sentinel_ip_port = []
        self.redis_ins = redis_ins
        self.redis_name = redis_name

    @property
    def get_redis_running_type(self):
        """
        判断redis实例的运行模式，非单机、烧饼、集群模式反馈default
        :return:
        """
        if self.redis_ins.redis_type == self.sentinel:
            return self.sentinel
        elif self.redis_ins.redis_type == self.standalone:
            return self.standalone
        elif self.redis_ins.redis_type == self.cluster:
            return self.cluster
        else:
            return "default"

    @property
    def get_all_redis_sentinel(self):
        """
        如是哨兵模式，获取哨兵实例所有实例地址及其端口信息
        :return: self.all_sentinel_ip_port 哨兵实例的地址和端口，self.all_ip_port redis实例的地址和端口
        """
        redis_sentinel = RunningInsSentinel.objects.all().filter(running_ins_name=self.redis_name).values()
        for redis_ip_port in redis_sentinel:
            ip_port = {}
            if redis_ip_port["redis_type"] != 'Redis-Sentinel':
                ip_port['redis_ip'] = redis_ip_port['redis_ip']
                ip_port['running_ins_port'] = redis_ip_port['running_ins_port']
                ip_port['redis_ins_mem'] = redis_ip_port['redis_ins_mem']
                ip_port['redis_ins'] = self.redis_ins
                ip_port['redis_type'] = 'Redis-Sentinel'
                self.all_ip_port.append(ip_port)
            else:
                ip_port['redis_ip'] = redis_ip_port['redis_ip']
                ip_port['running_ins_port'] = redis_ip_port['running_ins_port']
                self.all_sentinel_ip_port.append(ip_port)
        return self.all_sentinel_ip_port, self.all_ip_port

    @property
    def get_all_redis_cluster(self):
        """
        获取平台内所有集群模式的实例信息
        """
        redis_cluster = RunningInsCluster.objects.all().filter(running_ins_name=self.redis_name).values()
        for redis_ip_port in redis_cluster:
            ip_port = {'redis_ip': redis_ip_port['redis_ip'], 'running_ins_port': redis_ip_port['running_ins_port'],
                       'redis_ins_mem': redis_ip_port['redis_ins_mem'], 'redis_ins': self.redis_ins,
                       'redis_type': 'Redis-Cluster'}
            self.all_ip_port.append(ip_port)
        return self.all_ip_port

    @property
    def get_all_redis_standalone(self):
        """
        获取平台中所有单机实例的节点的信息
        """
        redis_standalone = RunningInsStandalone.objects.all().filter(running_ins_name=self.redis_name).values()
        for redis_standalone_ins in redis_standalone:
            ip_port = {'redis_ip': redis_standalone_ins['redis_ip'],
                       'running_ins_port': redis_standalone_ins['running_ins_port'],
                       'redis_ins_mem': redis_standalone_ins['redis_ins_mem'], 'redis_ins': self.redis_ins,
                       'redis_type': 'Redis-Standalone'}
            self.all_ip_port.append(ip_port)
        return self.all_ip_port


def get_all_redis_ins():
    """
    获取当前平台内所有的redis实例的ip和端口，用于监控使用
    :return: 所有redis实例的ip和端口的列表
    :type: list
    """
    all_sentinel_ip_port, all_ip_port = [], []
    running_ins_names = RunningInsTime.objects.all()
    all_redis_names = [running_ins_name.__dict__['running_ins_name'] for running_ins_name in running_ins_names]
    for redis_name in all_redis_names:
        redis_ins = running_ins_names.get(running_ins_name=redis_name)
        redis_name = redis_name
        ari = AllRedisIns(redis_name, redis_ins)
        # 尽早报错
        if ari.get_redis_running_type != redis_err_type:
            if ari.get_redis_running_type == sentinel:
                sentinel_ip_port, ip_port = ari.get_all_redis_sentinel
                all_sentinel_ip_port += sentinel_ip_port
                all_ip_port += ip_port
            elif ari.get_redis_running_type == cluster:
                ip_port = ari.get_all_redis_cluster
                all_ip_port += ip_port
            else:
                ip_port = ari.get_all_redis_standalone
                all_ip_port += ip_port
        else:
            pass
    logger.info(f"当前平台中所有的哨兵信息{all_sentinel_ip_port}, 所有的redis实例信息{all_ip_port}")
    return all_ip_port, all_sentinel_ip_port


class RedisMonitorTask:

    def __init__(self, redis_ins, redis_sentinel_ins, redis_mon):
        self.redis_used_memory_human = None
        self.redis_memory_usage = None
        self.redis_running_type = None
        self.redis_uptime_in_days = None
        self.redis_ins = redis_ins
        self.redis_mon = redis_mon
        self.redis_sentinel_ins = redis_sentinel_ins

    def redis_cluster_monitor_not_alive(self):
        now_status = get_redis_status(RunningInsCluster, self.redis_ins['redis_ins'].running_ins_name,
                                      self.redis_ins['redis_ip'],
                                      self.redis_ins['running_ins_port'])
        logger.error(
            f"02.实例{self.redis_ins['redis_ins'].running_ins_name}的运行模式{self.redis_ins['redis_type']},{self.redis_ins['redis_ip']}:{self.redis_ins['running_ins_port']}的数据库中的状态为{now_status}")
        if now_status != "未启动":
            set_redis_status(RunningInsCluster, self.redis_ins['redis_ins'].running_ins_name, "未启动",
                             self.redis_ins['redis_ip'],
                             self.redis_ins['running_ins_port'])
        cluster_alive_status = self.redis_mon.cluster_alive_status
        logger.error(
            f"实例{self.redis_ins['redis_ins'].running_ins_name}的运行模式{self.redis_ins['redis_type']},{self.redis_ins['redis_ip']}:{self.redis_ins['running_ins_port']}的集群存活状态为{cluster_alive_status}")

        if not cluster_alive_status or cluster_alive_status["cluster_state"] != "ok":
            RunningInsTime.objects.filter(running_ins_name=self.redis_ins['redis_ins'].running_ins_name).update(
                running_time=0, running_type="未运行")
            logger.error("集群实例{0}，未启动".format(self.redis_ins['redis_ins'].running_ins_name))

    def redis_sentinel_monitor_not_alive(self):

        RunningInsSentinel.objects.filter(redis_ip=self.redis_ins['redis_ip'],
                                          running_ins_port=self.redis_ins['running_ins_port']).update(
            redis_ins_alive="未启动")
        for sentinel_items in self.redis_sentinel_ins:
            redis_sentinel_mon = RedisScheduled(redis_ip=sentinel_items['redis_ip'],
                                                redis_port=sentinel_items['running_ins_port'])
            if not redis_sentinel_mon.redis_alive:
                RunningInsTime.objects.filter(running_ins_name=self.redis_ins['redis_ins'].running_ins_name).update(
                    running_time=0, running_type="未运行")
                logger.error("========哨兵实例{0} 未运行======".format(self.redis_ins['redis_ins'].running_ins_name))
            else:
                if redis_sentinel_mon.info & redis_sentinel_mon.info["master0"]["status"] != "ok":
                    RunningInsTime.objects.filter(
                        running_ins_name=self.redis_ins['redis_ins'].running_ins_name).update(
                        running_time=0, running_type="未运行")
                    logger.error("哨兵实例{0}， 未启动".format(self.redis_ins['redis_ins'].running_ins_name))

    def redis_standalone_monitor_not_alive(self):
        RunningInsStandalone.objects.filter(redis_ip=self.redis_ins['redis_ip'],
                                            running_ins_port=self.redis_ins['running_ins_port']).update(
            redis_ins_alive="未启动")
        RunningInsTime.objects.filter(running_ins_name=self.redis_ins['redis_ins'].running_ins_name).update(
            running_time=0, running_type="未运行")

    def redis_monitor_alive(self):
        redis_uptime_in_days = self.redis_mon.redis_uptime_in_days()
        if int(redis_uptime_in_days) == 0:
            self.redis_uptime_in_days = 1
        self.redis_running_type = self.redis_mon.redis_running_type()
        self.redis_memory_usage = self.redis_mon.redis_memory_usage()
        ops = self.redis_mon.ops()
        self.redis_used_memory_human = self.redis_mon.redis_used_memory_human()
        real_time_qps_obj = RealTimeQps(redis_used_mem=self.redis_used_memory_human,
                                        redis_qps=ops,
                                        redis_ins_used_mem=self.redis_memory_usage,
                                        collect_date=timezone.now,
                                        redis_running_monitor=self.redis_ins['redis_ins'],
                                        redis_ip=self.redis_ins['redis_ip'],
                                        redis_port=self.redis_ins['running_ins_port'],
                                        running_type="运行中")
        real_time_qps_obj.save()

    def redis_cluster_monitor_alive(self):
        cluster_alive_status = self.redis_mon.cluster_alive_status
        if cluster_alive_status:
            if cluster_alive_status["cluster_state"] == "ok":
                RunningInsTime.objects.filter(running_ins_name=self.redis_ins['redis_ins'].running_ins_name).update(
                    running_type="运行中",
                    running_ins_used_mem_rate=self.redis_memory_usage,
                    running_time=self.redis_uptime_in_days)
        RunningInsCluster.objects.filter(redis_ip=self.redis_ins['redis_ip'],
                                         running_ins_port=self.redis_ins['running_ins_port']).update(
            redis_type=self.redis_running_type,
            redis_ins_alive="运行中")
        # logger.info("当前实例{1}:{2}的角色是{0}".format(self.redis_running_type, self.redis_ins['redis_ip'],
        #                                                 self.redis_ins['running_ins_port']))

    def redis_sentinel_monitor_alive(self):
        RunningInsSentinel.objects.filter(redis_ip=self.redis_ins['redis_ip'],
                                          running_ins_port=self.redis_ins['running_ins_port']).update(
            redis_type=self.redis_running_type,
            redis_ins_alive="运行中")
        for sentinel_items in self.redis_sentinel_ins:
            redis_sentinel_mon = RedisScheduled(redis_ip=sentinel_items['redis_ip'],
                                                redis_port=sentinel_items['running_ins_port'])
            logger.info("sentinel_items:{0} \n redis_sentinel_mon:{1} \n redis_sentinel_mon.info:{2}".format(sentinel_items,
                                                                                                             redis_sentinel_mon.redis_alive,
                                                                                                             redis_sentinel_mon.info))
            if redis_sentinel_mon.redis_alive:
                RunningInsSentinel.objects.filter(redis_ip=sentinel_items['redis_ip'],
                                                  running_ins_port=sentinel_items['running_ins_port']).update(redis_ins_alive="运行中")
                if redis_sentinel_mon.info:
                    if redis_sentinel_mon.info["master0"]["status"] == "ok":
                        RunningInsTime.objects.filter(
                            running_ins_name=self.redis_ins['redis_ins'].running_ins_name).update(
                            running_time=self.redis_uptime_in_days, running_type="运行中")
                        if redis_sentinel_mon.info["master0"]["address"] == "{0}:{1}".format(self.redis_ins['redis_ip'],
                                                                                             self.redis_ins[
                                                                                                 'running_ins_port']):
                            RunningInsTime.objects.filter(
                                running_ins_name=self.redis_ins['redis_ins'].running_ins_name).update(
                                running_ins_used_mem_rate=self.redis_memory_usage)
                # logger.info("{0}:{1} 当前存活状态{2},入库状态{3}".format(sentinel_items['redis_ip'],
                #                                                          sentinel_items['running_ins_port'],
                #                                                          redis_sentinel_mon.redis_alive,
                #                                                          result))

    def redis_standalone_monitor_alive(self):
        RunningInsStandalone.objects.filter(redis_ip=self.redis_ins['redis_ip'],
                                            running_ins_port=self.redis_ins['running_ins_port']).update(
            redis_type=self.redis_running_type,
            redis_ins_alive="运行中")
        RunningInsTime.objects.filter(running_ins_name=self.redis_ins['redis_ins'].running_ins_name).update(
            running_time=self.redis_uptime_in_days,
            running_type="运行中",
            running_ins_used_mem_rate=self.redis_memory_usage)


def get_redis_ins_qps():
    """
    Redis ins 所有的redis实例进行监控
    TODO: 哨兵模式和集群模式的redis 角色变化监控，速率为现状是分钟级，需要精确到秒级。有优化方案的大佬请pull request万分感激。
    :return:
    """
    all_ip_port, all_sentienl_ip_port = get_all_redis_ins()
    for items in all_ip_port:
        try:
            redis_mon = RedisScheduled(redis_ip=items['redis_ip'], redis_port=items['running_ins_port'],
                                       redis_ins_mem=items['redis_ins_mem'], redis_ins=items['redis_ins'],
                                       password="qZr3pet")
            rmt = RedisMonitorTask(items, all_sentienl_ip_port, redis_mon)
            if not redis_mon.redis_alive:
                if items["redis_type"] == 'Redis-Cluster':
                    rmt.redis_cluster_monitor_not_alive()
                elif items["redis_type"] == 'Redis-Sentinel':
                    rmt.redis_sentinel_monitor_not_alive()
                else:
                    rmt.redis_standalone_monitor_not_alive()
                logger.error("实例{0}监控异常,运行模式{1} {2}::::{3}".format(items['redis_ins'], items['redis_type'],
                                                                             items['redis_ip'],
                                                                             items['running_ins_port']))
            else:
                rmt.redis_monitor_alive()

                if items["redis_type"] == 'Redis-Cluster':
                    rmt.redis_cluster_monitor_alive()
                elif items["redis_type"] == 'Redis-Sentinel':
                    rmt.redis_sentinel_monitor_alive()
                else:
                    rmt.redis_standalone_monitor_alive()
        except ValueError as e:
            logger.error("报错信息为{0}".format(e))
        finally:
            pass


t = threading.Thread(target=get_redis_ins_qps, name='get_redis_ins_qps')
t.start()
t.join()
