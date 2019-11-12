import redis
import time
# from .tasks import mem_unit_chage
from .models import RealTimeQps
from django.utils import timezone


class RedisScheduled(object):

    def __init__(self, redis_ip, redis_port, redis_ins_mem, redis_ins):
        self.redis_ip = redis_ip
        self.redis_port = redis_port
        self.redis_ins_mem = redis_ins_mem
        self.redis_ins = redis_ins

    def redismonitor(self):
        redis_pyhon_ins = redis.ConnectionPool(host=self.redis_ip, port=self.redis_port)
        redis_pool = redis.Redis(connection_pool=redis_pyhon_ins)
        i = 0
        try:
            while i < 60:
                qps = redis_pool.info()
                used_memory_human = qps['used_memory_human']
                redis_ins_used_mem = mem_unit_chage(used_memory_human) / mem_unit_chage(self.redis_ins_mem)
                time.sleep(1)
                print("{0},Redis的QPS为{1},已用内存{2},内存使用率{3},端口为{4}".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                                                                         qps['instantaneous_ops_per_sec'],
                                                                         used_memory_human, float('%.2f' % redis_ins_used_mem), self.redis_port))
                real_time_qps_obj = RealTimeQps(redis_used_mem=used_memory_human,
                                                redis_qps=qps['instantaneous_ops_per_sec'],
                                                redis_ins_used_mem=float('%.2f' % redis_ins_used_mem),
                                                collect_date=timezone.now,
                                                redis_running_monitor=self.redis_ins)
                real_time_qps_obj.save()
                i += 1
        except ConnectionRefusedError:
            pass


def mem_unit_chage(mem):
    memory = mem[0:-1]
    type = mem[-1]
    if type == 'g' or 'G':
        return int(float(memory)*1024)
    elif type == 'k' or 'K':
        return int(float(memory)/1024)
    else:
        return int(float(memory))
