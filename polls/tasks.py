import time
import redis
from .models import RealTimeQps, RunningInsTime, RunningInsSentinel, RunningInsStandalone
from django.utils import timezone
from .scheduled import RedisScheduled
import threading


def get_redis_ins_qps():
    """
    Redis ins 所有的redis实例进行监控，速率为秒级
    :return:
    """
    running_ins_names = RunningInsTime.objects.all()
    all_redis_names = [running_ins_name.__dict__['running_ins_name'] for running_ins_name in running_ins_names]
    all_ip_port = []
    for redis_name in all_redis_names:
        try:
            redis_ins = running_ins_names.get(running_ins_name=redis_name)
            if redis_ins.redis_type == 'Redis-Sentinel':
                redis_sentinel = RunningInsSentinel.objects.all()
                for redis_ip_port in redis_sentinel:
                    ip_port = {}
                    if redis_ip_port.redis_type != 'Redis-Sentinel':
                        ip_port['redis_ip'] = redis_ip_port.__dict__['redis_ip']
                        ip_port['running_ins_port'] = redis_ip_port.__dict__['running_ins_port']
                        ip_port['redis_ins_mem'] = redis_ip_port.__dict__['redis_ins_mem']
                        ip_port['redis_ins'] = redis_ins
                        all_ip_port.append(ip_port)
            elif redis_ins.redis_type == 'Redis-Standalone':
                redis_standalone = RunningInsStandalone.objects.all()
                for redis_ip_port in redis_standalone:
                    ip_port = {}
                    ip_port['redis_ip'] = redis_ip_port.__dict__['redis_ip']
                    ip_port['running_ins_port'] = redis_ip_port.__dict__['running_ins_port']
                    ip_port['redis_ins_mem'] = redis_ip_port.__dict__['redis_ins_mem']
                    ip_port['redis_ins'] = redis_ins
                    all_ip_port.append(ip_port)
            for items in all_ip_port:
                redis_mon = RedisScheduled(redis_ip=items['redis_ip'], redis_port=items['running_ins_port'],
                                           redis_ins_mem=items['redis_ins_mem'], redis_ins=items['redis_ins'])
                redis_mon.redismonitor()
        except redis.exceptions.ConnectionError as e:
            print(e)
        continue


t = threading.Thread(target=get_redis_ins_qps, name='get_redis_ins_qps')
t.start()
t.join()
