import redis
import time
# from .tasks import mem_unit_chage
from .models import RealTimeQps, RunningInsTime
from django.utils import timezone


class RedisScheduled(object):

    def __init__(self, redis_ip, redis_port, redis_ins_mem, redis_ins):
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

    def redismonitor(self):
        """
        链接redis实例，获取qps、内存使用率并将数据入库
        :return:
        """
        redis_pyhon_ins = redis.ConnectionPool(host=self.redis_ip, port=self.redis_port)
        redis_pool = redis.Redis(connection_pool=redis_pyhon_ins)
        try:
            qps = redis_pool.info()
            used_memory_human = qps['used_memory_human']
            uptime_in_days = qps['uptime_in_days']
            i = 0
            while i < 60:
                redis_ins_used_mem = mem_unit_chage(used_memory_human) / mem_unit_chage(self.redis_ins_mem)
                time.sleep(1)
                print("{0},Redis的QPS为{1},已用内存{2},内存使用率{3},端口为{4},运行天数{5}".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                                                                         qps['instantaneous_ops_per_sec'],
                                                                         used_memory_human, float('%.2f' % redis_ins_used_mem), self.redis_port, uptime_in_days))
                real_time_qps_obj = RealTimeQps(redis_used_mem=used_memory_human,
                                                redis_qps=qps['instantaneous_ops_per_sec'],
                                                redis_ins_used_mem=float('%.2f' % redis_ins_used_mem),
                                                collect_date=timezone.now,
                                                redis_running_monitor=self.redis_ins,
                                                redis_ip=self.redis_ip,
                                                redis_port=self.redis_port)
                real_time_qps_obj.save()
                i += 1
                RunningInsTime.objects.filter(running_ins_name=self.redis_ins.running_ins_name).update(
                    running_time=uptime_in_days, running_ins_used_mem_rate=redis_ins_used_mem)
        except ConnectionError as e:
            RunningInsTime.objects.filter(running_ins_name=self.redis_ins.running_ins_name).update(
                running_time="未启动")
            print("ConnectionRefusedError: {0}".format(e))
        finally:
            pass


def mem_unit_chage(mem):
    """
    将内存大小换算为m为单位
    :param mem:
    :return:
    """
    memory = mem[0:-1]
    type = mem[-1]
    if type == 'g' and 'G':
        return int(float(memory)*1024)
    elif type == 'k' and 'K':
        return int(float(memory)/1024)
    else:
        return int(float(memory))
