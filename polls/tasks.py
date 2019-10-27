import time
import redis
from .models import RunningInsTime


# class RedisWatch(object):
#
#     def __init__(self, obj):
#
#         self.redis_ins_ip = [redis_ins_ip.__dict__ for redis_ins_ip in obj]
#         self.redis_pyhon_ins = redis.ConnectionPool(host="127.0.0.1", port=32769)
#         self.redis_pool = redis.Redis(connection_pool=self.redis_pyhon_ins)
#
#     def get_redis_ins_qps(self):
#         qps = self.redis_pool.info()
#         time.sleep(1)
#         print(qps['instantaneous_ops_per_sec'])
#         return qps['instantaneous_ops_per_sec']


def get_redis_ins_qps():
    obj = RunningInsTime.objects.all()
    print(obj)
    redis_pyhon_ins = redis.ConnectionPool(host="127.0.0.1", port=32769)
    redis_pool = redis.Redis(connection_pool=redis_pyhon_ins)
    i = 0
    while i < 60:
        qps = redis_pool.info()
        time.sleep(1)
        print("{0},Redis的QPS为{1}".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                                         qps['instantaneous_ops_per_sec']))
        i += 1
