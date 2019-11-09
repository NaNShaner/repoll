import time
import redis
from .models import RealTimeQps, RunningInsTime
from django.utils import timezone


def get_redis_ins_qps():
    """
    Redis ins 所有的redis实例进行监控，速率为秒级
    :return:
    """
    running_ins_names = RunningInsTime.objects.all()
    all_redis_names = [running_ins_name.__dict__['running_ins_name'] for running_ins_name in running_ins_names]
    try:
        for redis_name in all_redis_names:
            redis_ins_all = running_ins_names.filter(running_ins_name=redis_name)
            redis_ins = running_ins_names.get(running_ins_name=redis_name)
            redis_id = redis_ins_all.values('id').first()['id']
            redis_ip = redis_ins_all.values('redis_ip').first()['redis_ip']
            redis_port = redis_ins_all.values('running_ins_port').first()['running_ins_port']
            redis_ins_mem = redis_ins_all.values('redis_ins_mem').first()['redis_ins_mem']
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
                real_time_qps_obj.save()
                i += 1
    except IOError as e:
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
