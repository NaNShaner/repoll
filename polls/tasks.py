import time
import redis
from .models import RealTimeQps, RunningInsTime
from django.utils import timezone


# class RedisWatch(object):
#
#     def __init__(self, obj):
#
#         self.redis_ins_ip = [redis_ins_ip.__dict__ for redis_ins_ip in obj]
#         self.redis_pyhon_ins = redis.ConnectionPool(host="127.0.0.1", port=32769)
#         self.redis_pool = redis.Redis(connection_pool=self.redis_pyhon_ins)
#
#     def get_redis_ins_qps(self):ls
#         qps = self.redis_pool.info()
#         time.sleep(1)
#         print(qps['instantaneous_ops_per_sec'])
#         return qps['instantaneous_ops_per_sec']


def get_redis_ins_qps():
    running_ins_names = RunningInsTime.objects.all()
    # running_ins_time_id = RunningInsTime.objects.all().filter(running_ins_name=)
    all_redis_names = [running_ins_name.__dict__['running_ins_name'] for running_ins_name in running_ins_names]
    for redis_name in all_redis_names:
        redis_ins_all = running_ins_names.filter(running_ins_name=redis_name)
        redis_ins = running_ins_names.get(running_ins_name=redis_name)
        redis_id = redis_ins_all.values('id').first()['id']
        redis_ip = redis_ins_all.values('redis_ip').first()['redis_ip']
        redis_port = redis_ins_all.values('running_ins_port').first()['running_ins_port']
        redis_ins_mem = redis_ins_all.values('redis_ins_mem').first()['redis_ins_mem']
        print("redis_port{0},{1}".format(redis_port, type(redis_port)))
        print("redis_ip{0},{1}".format(redis_ip, type(redis_ip)))
        print("redis_ins_mem{0},{1}".format(redis_ins_mem, type(redis_ins_mem)))
        print("redis_id{0},{1}".format(redis_id, type(redis_id)))
        redis_pyhon_ins = redis.ConnectionPool(host=redis_ip, port=redis_port)
        redis_pool = redis.Redis(connection_pool=redis_pyhon_ins)
        i = 0
        while i < 60:
            qps = redis_pool.info()
            used_memory_human = qps['used_memory_human']
            redis_ins_used_mem = mem_unit_chage(used_memory_human) / mem_unit_chage(redis_ins_mem)
            time.sleep(1)
            print("{0},Redis的QPS为{1},已用内存{2},内存使用率{3}".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                                                              qps['instantaneous_ops_per_sec'],
                                                              used_memory_human, float('%.2f' % redis_ins_used_mem)))
            real_time_qps_obj = RealTimeQps(redis_used_mem=used_memory_human,
                                            redis_qps=qps['instantaneous_ops_per_sec'],
                                            redis_ins_used_mem=float('%.2f' % redis_ins_used_mem),
                                            collect_date=timezone.now,
                                            redis_running_monitor=redis_ins)
            save_status = real_time_qps_obj.save()
            print(real_time_qps_obj, save_status)
            i += 1


def mem_unit_chage(mem):
    memory = mem[0:-1]
    type = mem[-1]
    if type == 'g' or 'G':
        return float(memory)*1024
    else:
        return float(memory)
