import redis
import time
from .models import RealTimeQps, RunningInsTime
from django.utils import timezone
import logging
logger = logging.getLogger("redis.monitor")


class RedisScheduled(object):

    def __init__(self, redis_ip, redis_port, redis_ins_mem=None, redis_ins=None, password=None):
        """
        IP、port、最大内存以及redis已运行实例obj
        :param redis_ip:
        :param redis_port:
        :param redis_ins_mem:
        :param redis_ins:
        """
        self.redis_ip = redis_ip
        self.redis_port = redis_port
        self.redis_ins_mem = redis_ins_mem
        self.redis_ins = redis_ins
        self.password = password
        if self.password:
            self.rds = redis.StrictRedis(host=self.redis_ip, port=self.redis_port, password=self.password)
        else:
            self.rds = redis.StrictRedis(host=self.redis_ip, port=self.redis_port)
        try:
            self.info = self.rds.info()
        except Exception as e:
            logger.error("实例{0}:{1}  执行redis info命令失败，报错信息为{2}".format(self.redis_ip, self.redis_port, e))
            self.info = None

    def redismonitor(self):
        """
        链接redis实例，获取qps、内存使用率并将数据入库
        :return:
        """
        try:
            if self.info:
                used_memory_human = self.info['used_memory_human']
                uptime_in_days = self.info['uptime_in_days']
                i = 0
                while i < 60:
                    redis_ins_used_mem = mem_unit_chage(used_memory_human) / mem_unit_chage(self.redis_ins_mem)
                    time.sleep(1)
                    print("{0},Redis的QPS为{1},已用内存{2},内存使用率{3},端口为{4},运行天数{5}".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                                                                             self.info['instantaneous_ops_per_sec'],
                                                                             used_memory_human, float('%.2f' % redis_ins_used_mem), self.redis_port, uptime_in_days))
                    real_time_qps_obj = RealTimeQps(redis_used_mem=used_memory_human,
                                                    redis_qps=self.info['instantaneous_ops_per_sec'],
                                                    redis_ins_used_mem=float('%.2f' % redis_ins_used_mem),
                                                    collect_date=timezone.now,
                                                    redis_running_monitor=self.redis_ins,
                                                    redis_ip=self.redis_ip,
                                                    redis_port=self.redis_port)
                    real_time_qps_obj.save()
                    i += 1
                    RunningInsTime.objects.filter(running_ins_name=self.redis_ins.running_ins_name).update(
                        running_time=uptime_in_days, running_ins_used_mem_rate=redis_ins_used_mem)
            else:
                RunningInsTime.objects.filter(running_ins_name=self.redis_ins.running_ins_name).update(
                    running_time="未启动")
        except ConnectionError as e:
            RunningInsTime.objects.filter(running_ins_name=self.redis_ins.running_ins_name).update(
                running_time="未启动")
            print("ConnectionRefusedError: {0}".format(e))

    def redis_connections(self):
        """
        redis connected_clients
        :return:
        """
        try:
            return self.info['connected_clients']
        except Exception as e:
            return 0

    def redis_connections_usage(self):
        """
        redis 链接使用率
        :return:
        """
        try:
            curr_connections = self.redis_connections()
            max_clients = self.parse_config('maxclients')
            rate = float(curr_connections) / float(max_clients)
            return "%.2f" % (rate * 100)
        except Exception as e:
            return 0

    def redis_used_memory(self):
        """
        redis 已用内存
        :return:
        """
        try:
            return self.info['used_memory']
        except Exception as e:
            return 0

    def redis_used_memory_human(self):
        """
        redis 已用内存，已正常可读性
        :return:
        """
        try:
            return self.info['used_memory_human']
        except Exception as e:
            return 0

    def redis_memory_usage(self):
        """
        redis 已用内存使用率
        :return:
        """
        try:
            used_memory = self.info['used_memory']
            max_memory = self.rds.config_get('maxmemory')
            if max_memory:
                rate = float(used_memory) / float(max_memory['maxmemory'])
            else:
                return 0
            return "%.2f" % (rate * 100)
        except Exception as e:
            return 0

    @property
    def redis_alive(self):
        """
        redis 是否存活
        :return:
        """
        try:
            return self.rds.ping()
        except Exception as e:
            return False

    def rejected_connections(self):
        """
        redis 堵塞链接
        :return:
        """
        try:
            return self.info['rejected_connections']
        except Exception as e:
            return None

    def evicted_keys(self):
        """
        redis 驱逐key的数量
        :return:
        """
        try:
            return self.info['evicted_keys']
        except Exception as e:
            return None

    def blocked_clients(self):
        """
        堵塞客户端
        :return:
        """
        try:
            return self.info['blocked_clients']
        except Exception as e:
            return None

    def ops(self):
        """
        每秒处理指令数
        :return:
        """
        try:
            return self.info['instantaneous_ops_per_sec']
        except Exception as e:
            return None

    def hit_rate(self):
        """
        命令命中率
        :return:
        """
        try:
            misses = self.info['keyspace_misses']
            hits = self.info['keyspace_hits']
            rate = float(hits) / float(int(hits) + int(misses))
            return "%.2f" % (rate * 100)
        except Exception as e:
            return 0

    def redis_running_type(self):
        """
        命令命中率
        :return:
        """
        try:
            choice_list = ['Redis-Master', 'Redis-Slave']
            if self.info['role'] == "master":
                return choice_list[0]
            elif self.info['role'] == "slave":
                return choice_list[1]
            else:
                return 0
        except Exception as e:
            return 0

    def redis_uptime_in_days(self):
        """
        redis 已运行天数
        :return:
        """
        try:
            uptime_in_days = self.info['uptime_in_days']
            return uptime_in_days
        except Exception as e:
            return 0

    def parse_config(self, type):
        """
        从存活的redis实例中，获取配置参数
        :param type:
        :return:
        """
        try:
            return self.rds.config_get(type)[type]
        except Exception as e:
            return None

    def set_config(self, command, value):
        """
        通过 config set命令行实时设置
        :param command:
        :param value:
        :return:
        """
        try:
            return self.rds.config_set(name=command, value=value)
        except Exception as e:
            return None

    @property
    def cluster_alive_status(self):
        """
        获取集群的info信息，等同cluster info的命令行命令返回
        :return:
        """
        try:
            return self.rds.cluster("info")
        except Exception as e:
            return None


def mem_unit_chage(mem):
    """
    将内存大小换算为m为单位
    :param mem:
    :return:
    """
    memory = mem[0:-1]
    memory_type = mem[-1]
    if memory_type == 'g' and 'G':
        return int(float(memory)*1024)
    elif memory_type == 'k' and 'K':
        return int(float(memory)/1024)
    elif memory_type == 'm' and 'M':
        return int(float(memory)/1024)
    else:
        return int(float(mem))
