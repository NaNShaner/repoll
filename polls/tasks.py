import time
import redis
from .models import RunningInsTime, RunningInsSentinel, RunningInsStandalone, RunningInsCluster, RealTimeQps
from django.utils import timezone
from .scheduled import RedisScheduled
import threading
import logging

# 日志格式
logging.basicConfig(filename="repoll.log", filemode="a+",
                    format="%(asctime)s %(name)s: %(levelname)s: %(message)s", datefmt="%Y-%M-%d %H:%M:%S",
                    level=logging.INFO)


def get_redis_ins_qps():
    """
    Redis ins 所有的redis实例进行监控，速率为秒级
    FIXME: 遍历库中的redis，使用redis.py 链接报错无法再继续
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
            elif redis_ins.redis_type == 'Redis-Cluster':
                redis_cluster = RunningInsCluster.objects.all()
                for redis_ip_port in redis_cluster:
                    ip_port = {}
                    ip_port['redis_ip'] = redis_ip_port.__dict__['redis_ip']
                    ip_port['running_ins_port'] = redis_ip_port.__dict__['running_ins_port']
                    ip_port['redis_ins_mem'] = redis_ip_port.__dict__['redis_ins_mem']
                    ip_port['redis_ins'] = redis_ins
                    all_ip_port.append(ip_port)
        except redis.exceptions.ConnectionError as e:
            logging.error(e)

        for items in all_ip_port:
            try:
                redis_mon = RedisScheduled(redis_ip=items['redis_ip'], redis_port=items['running_ins_port'],
                                           redis_ins_mem=items['redis_ins_mem'], redis_ins=items['redis_ins'])
                if not redis_mon.redis_alive:
                    RunningInsTime.objects.filter(running_ins_name=items['redis_ins'].running_ins_name).update(
                        running_time=0, running_type="未运行")
                    logging.error("实例{0}监控异常".format(items['redis_ins']))
                else:
                    redis_memory_usage = redis_mon.redis_memory_usage()
                    ops = redis_mon.ops()
                    redis_used_memory_human = redis_mon.redis_used_memory_human()
                    redis_uptime_in_days = redis_mon.redis_uptime_in_days()
                    logging.info("{0},{1},{2},{3}".format(redis_memory_usage, ops, redis_used_memory_human, redis_uptime_in_days))
                    real_time_qps_obj = RealTimeQps(redis_used_mem=redis_used_memory_human,
                                                    redis_qps=ops,
                                                    redis_ins_used_mem=redis_memory_usage,
                                                    collect_date=timezone.now,
                                                    redis_running_monitor=items['redis_ins'],
                                                    redis_ip=items['redis_ip'],
                                                    redis_port=items['running_ins_port'],
                                                    running_type="运行中")
                    real_time_qps_obj.save()
                    RunningInsTime.objects.filter(running_ins_name=items['redis_ins'].running_ins_name).update(
                        running_type="运行中",
                        running_ins_used_mem_rate=redis_memory_usage,
                        running_time=redis_uptime_in_days)
            except ValueError as e:
                logging.error(e)
            finally:
                logging.info("finally : {0}".format(items))


t = threading.Thread(target=get_redis_ins_qps, name='get_redis_ins_qps')
t.start()
t.join()
