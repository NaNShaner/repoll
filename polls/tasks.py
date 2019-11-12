import time
import redis
from .models import RealTimeQps, RunningInsTime
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

    for redis_name in all_redis_names:
        try:
            redis_ins_all = running_ins_names.filter(running_ins_name=redis_name)
            redis_ins = running_ins_names.get(running_ins_name=redis_name)
            # redis_id = redis_ins_all.values('id').first()['id']
            redis_ip = redis_ins_all.values('redis_ip').first()['redis_ip']
            redis_port = redis_ins_all.values('running_ins_port').first()['running_ins_port']
            redis_ins_mem = redis_ins_all.values('redis_ins_mem').first()['redis_ins_mem']
            redis_mon = RedisScheduled(redis_ip=redis_ip, redis_port=redis_port,
                                       redis_ins_mem=redis_ins_mem, redis_ins=redis_ins)
            redis_mon.redismonitor()
        except redis.exceptions.ConnectionError:
            pass
        continue


t = threading.Thread(target=get_redis_ins_qps, name='get_redis_ins_qps')
t.start()
t.join()
