import time
import redis
from .models import RunningInsTime, RunningInsSentinel, RunningInsStandalone, RunningInsCluster, RealTimeQps
from django.utils import timezone
from .scheduled import RedisScheduled
import threading
import logging

# 日志格式
# logging.basicConfig(format="%(asctime)s %(name)s: %(levelname)s: %(message)s",
#                     level=logging.INFO)


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
                redis_sentinel = RunningInsSentinel.objects.all().filter(running_ins_name=redis_name).values()
                ip_port = {}
                for redis_ip_port in redis_sentinel:
                    if redis_ip_port.redis_type != 'Redis-Sentinel':
                        ip_port['redis_ip'] = redis_ip_port['redis_ip']
                        ip_port['running_ins_port'] = redis_ip_port['running_ins_port']
                        ip_port['redis_ins_mem'] = redis_ip_port['redis_ins_mem']
                        ip_port['redis_ins'] = redis_ins
                        all_ip_port.append(ip_port)
            elif redis_ins.redis_type == 'Redis-Standalone':
                redis_standalone = RunningInsStandalone.objects.all().filter(running_ins_name=redis_name).values()
                ip_port = {}
                for redis_standalone_ins in redis_standalone:
                    ip_port['redis_ip'] = redis_standalone_ins['redis_ip']
                    ip_port['running_ins_port'] = redis_standalone_ins['running_ins_port']
                    ip_port['redis_ins_mem'] = redis_standalone_ins['redis_ins_mem']
                    ip_port['redis_ins'] = redis_ins
                    all_ip_port.append(ip_port)
            elif redis_ins.redis_type == 'Redis-Cluster':
                redis_cluster = RunningInsCluster.objects.all().filter(running_ins_name=redis_name).values()
                ip_port = {}
                for redis_ip_port in redis_cluster:
                    ip_port['redis_ip'] = redis_ip_port['redis_ip']
                    ip_port['running_ins_port'] = redis_ip_port['running_ins_port']
                    ip_port['redis_ins_mem'] = redis_ip_port['redis_ins_mem']
                    ip_port['redis_ins'] = redis_ins
                    all_ip_port.append(ip_port)
        except redis.exceptions.ConnectionError as e:
            print("报错信息为".format(e))
        # print(all_ip_port)
        for items in all_ip_port:
            try:
                redis_mon = RedisScheduled(redis_ip=items['redis_ip'], redis_port=items['running_ins_port'],
                                           redis_ins_mem=items['redis_ins_mem'], redis_ins=items['redis_ins'])
                if not redis_mon.redis_alive:
                    RunningInsTime.objects.filter(running_ins_name=items['redis_ins'].running_ins_name).update(
                        running_time=0, running_type="未运行")
                    print("实例{0}监控异常, {1}::::{2}".format(items['redis_ins'], items['redis_ip'], items['running_ins_port']))
                else:
                    redis_memory_usage = redis_mon.redis_memory_usage()
                    ops = redis_mon.ops()
                    redis_used_memory_human = redis_mon.redis_used_memory_human()
                    redis_uptime_in_days = redis_mon.redis_uptime_in_days()
                    if int(redis_uptime_in_days) == 0:
                        redis_uptime_in_days = 1
                    real_time_qps_obj = RealTimeQps(redis_used_mem=redis_used_memory_human,
                                                    redis_qps=ops,
                                                    redis_ins_used_mem=redis_memory_usage,
                                                    collect_date=timezone.now,
                                                    redis_running_monitor=items['redis_ins'],
                                                    redis_ip=items['redis_ip'],
                                                    redis_port=items['running_ins_port'],
                                                    running_type="运行中")
                    real_time_qps_obj.save()
                    qw = RunningInsTime.objects.filter(running_ins_name=items['redis_ins'].running_ins_name).update(
                        running_type="运行中",
                        running_ins_used_mem_rate=redis_memory_usage,
                        running_time=redis_uptime_in_days)
                    # print("items['redis_ins']: {0}".format(items['redis_ins'].running_ins_name))
                    print("实例名称：{7} -- {4}:::{5} -- RunningInsTime保存状态:{6} -- redis_memory_usage:{0},ops:{1},redis_used_memory_human:{2},redis_uptime_in_days:{3}".format(
                            redis_memory_usage, ops, redis_used_memory_human, redis_uptime_in_days, items['redis_ip'],
                            items['running_ins_port'], qw, items['redis_ins'].running_ins_name))
            except ValueError as e:
                print("报错信息为{0}".format(e))


t = threading.Thread(target=get_redis_ins_qps, name='get_redis_ins_qps')
t.start()
t.join()
