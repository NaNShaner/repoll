from .models import RunningInsTime, RunningInsSentinel, RunningInsStandalone, RunningInsCluster
from .handlers import RedisStartClass
from .scheduled import RedisScheduled
from django.http import HttpResponse
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions


class RunningInsTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RunningInsTime
        fields = '__all__'


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def redisstop(request, redis_type, ins_id):
    """
    API接口，停止redis实例。
    授权模式，当前平台内部用户
    """
    if redis_type == 'sentinel':
        running_ins_time = RunningInsSentinel.objects.all()
    elif redis_type == 'standalone':
        running_ins_time = RunningInsStandalone.objects.all()
    elif redis_type == 'cluster':
        running_ins_time = RunningInsCluster.objects.all()
    running_ins = running_ins_time.filter(id=ins_id)
    running_ins_ip = running_ins.values('redis_ip').first()
    running_ins_port = running_ins.values('running_ins_port').first()
    redisins = RedisStartClass(host=running_ins_ip['redis_ip'],
                               redis_server_ctl="/opt/repoll/redis/src/redis-cli -p {0} shutdown".format(running_ins_port['running_ins_port']))
    serializer = RunningInsTimeSerializer(running_ins, many=True)
    result = serializer.data[0]
    if redisins.start_server():
        result['redis_status'] = "DOWN"
        if redis_type == 'sentinel':
            RunningInsSentinel.objects.filter(redis_ip=running_ins_ip['redis_ip'],
                                              running_ins_port=running_ins_port['running_ins_port']).update(
                redis_ins_alive="未启动")
        elif redis_type == 'standalone':
            RunningInsStandalone.objects.filter(redis_ip=running_ins_ip['redis_ip'],
                                                running_ins_port=running_ins_port['running_ins_port']).update(
                redis_ins_alive="未启动")
        elif redis_type == 'cluster':
            RunningInsCluster.objects.filter(redis_ip=running_ins_ip['redis_ip'],
                                             running_ins_port=running_ins_port['running_ins_port']).update(
                redis_ins_alive="未启动")
        return Response(result)
    result['redis_status'] = "ERROR"
    return Response(result)


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def redisstart(request, redis_type, ins_id):
    """
    API接口，启动redis实例。
    授权模式，当前平台内部用户
    """
    if redis_type == 'sentinel':
        running_ins_time = RunningInsSentinel.objects.all()
    elif redis_type == 'standalone':
        running_ins_time = RunningInsStandalone.objects.all()
    elif redis_type == 'cluster':
        running_ins_time = RunningInsCluster.objects.all()
    running_ins = running_ins_time.filter(id=ins_id)
    running_ins_ip = running_ins.values('redis_ip').first()
    running_ins_port = running_ins.values('running_ins_port').first()
    for c in running_ins:
        running_ins_type = c.__dict__['redis_type']
    if running_ins_type == 'Redis-Sentinel':
        redisins = RedisStartClass(host=running_ins_ip['redis_ip'],
                                   redis_server_ctl="/opt/repoll/redis/src/redis-server /opt/repoll/conf/{0}-sentienl.conf --sentinel".format(
                                       running_ins_port['running_ins_port']))
    else:
        if redis_type == 'cluster':
            redisins = RedisStartClass(host=running_ins_ip['redis_ip'],
                                       redis_server_ctl="/opt/repoll/redis/src/redis-server /opt/repoll/conf/{0}-cluster.conf".format(
                                           running_ins_port['running_ins_port']))
        else:
            redisins = RedisStartClass(host=running_ins_ip['redis_ip'],
                                       redis_server_ctl="/opt/repoll/redis/src/redis-server /opt/repoll/conf/{0}.conf".format(
                                           running_ins_port['running_ins_port']))
    serializer = RunningInsTimeSerializer(running_ins, many=True)
    result = serializer.data[0]
    if redisins.start_server():
        result['redis_status'] = "UP"
        if redis_type == 'sentinel':
            RunningInsSentinel.objects.filter(redis_ip=running_ins_ip['redis_ip'],
                                              running_ins_port=running_ins_port['running_ins_port']).update(
                redis_ins_alive="运行中")
        elif redis_type == 'standalone':
            RunningInsStandalone.objects.filter(redis_ip=running_ins_ip['redis_ip'],
                                                running_ins_port=running_ins_port['running_ins_port']).update(
                redis_ins_alive="运行中")
        elif redis_type == 'cluster':
            RunningInsCluster.objects.filter(redis_ip=running_ins_ip['redis_ip'],
                                             running_ins_port=running_ins_port['running_ins_port']).update(
                redis_ins_alive="运行中")
        return Response(result)
    result['redis_status'] = "ERROR"
    return Response(result)


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def allredisins(request, redis_type=None):
    """
    API接口，获取平台内所有redis实例。
    授权模式，当前平台内部用户
    """
    sentinel_ins_time = RunningInsSentinel.objects.all()
    stanalone_ins_time = RunningInsStandalone.objects.all()
    cluster_ins_time = RunningInsCluster.objects.all()
    all_redis_ins_list = []
    try:
        if redis_type == "all":
            sentinel_ins = sentinel_ins_time.values('redis_ip', 'running_ins_port', 'redis_ins_alive',
                                                    'redis_ins_mem', 'redis_type', 'running_ins_name',)
            stanalone_ins = stanalone_ins_time.values('redis_ip', 'running_ins_port', 'redis_ins_alive',
                                                      'redis_ins_mem', 'redis_type', 'running_ins_name')
            cluster_ins = cluster_ins_time.values('redis_ip', 'running_ins_port', 'redis_ins_alive',
                                                  'redis_ins_mem', 'redis_type', 'running_ins_name')
            all_redis_ins_list = list(sentinel_ins) + list(stanalone_ins) + list(cluster_ins)
        elif redis_type == "standalone":
            stanalone_ins = stanalone_ins_time.values('redis_ip', 'running_ins_port', 'redis_ins_alive',
                                                      'redis_ins_mem', 'redis_type', 'running_ins_name')
            all_redis_ins_list = list(stanalone_ins)
        elif redis_type == "sentinel":
            sentinel_ins = sentinel_ins_time.values('redis_ip', 'running_ins_port', 'redis_ins_alive',
                                                    'redis_ins_mem', 'redis_type', 'running_ins_name')
            all_redis_ins_list = list(sentinel_ins)
        elif redis_type == "cluster":
            cluster_ins = cluster_ins_time.values('redis_ip', 'running_ins_port', 'redis_ins_alive',
                                                  'redis_ins_mem', 'redis_type', 'running_ins_name')
            all_redis_ins_list = list(cluster_ins)
    except IOError as e:
        return Response("redisins 获取平台内所有redis实例接口报错，报错信息{0}".format(e))
    return Response(all_redis_ins_list)


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def memory_action(request, redis_type, redis_ins_name, memory):
    """
    API接口，获取内存扩缩容。
    授权模式，当前平台内部用户
    """
    running_redis_obj = RunningInsTime.objects.all()
    redis_ins_status = True
    try:
        if redis_type == "Redis-Standalone":
            obj = RunningInsStandalone.objects.all()
            redis_ins_ip_port = obj.filter(running_ins_name=redis_ins_name).values("redis_ip", "running_ins_port")
            redis_mon = RedisScheduled(redis_ip=redis_ins_ip_port[0]['redis_ip'],
                                       redis_port=redis_ins_ip_port[0]['running_ins_port'])
            serializer = RunningInsTimeSerializer(obj.filter(running_ins_name=redis_ins_name), many=True)
            result = serializer.data[0]
            if redis_mon.set_config(command="maxmemory", value=memory):
                result['set_redis_mem'] = True
                obj.filter(running_ins_name=redis_ins_name).update(redis_ins_mem=memory)
                running_redis_obj.filter(running_ins_name=redis_ins_name).update(redis_ins_mem=memory)
                result['reason'] = "{0}实例运行扩缩容正常".format(redis_ins_name)
            else:
                result['set_redis_mem'] = False
                result['reason'] = "{0}实例运行状态异常请检查".format(redis_ins_name)
            return Response(result)
        elif redis_type == "Redis-Cluster":
            obj = RunningInsCluster.objects.all()
            running_status_redis_obj = running_redis_obj.filter(running_ins_name=redis_ins_name).values('running_type')
            redis_ins_ip_port = obj.filter(running_ins_name=redis_ins_name).values("redis_ip", "running_ins_port")
            serializer = RunningInsTimeSerializer(obj.filter(running_ins_name=redis_ins_name), many=True)
            result = serializer.data[0]
            redis_ins_status = True
            if running_status_redis_obj[0]['running_type'] == "运行中":
                for ins_ip_port in redis_ins_ip_port:
                    redis_mon = RedisScheduled(redis_ip=ins_ip_port["redis_ip"],
                                               redis_port=ins_ip_port["running_ins_port"])
                    redis_mon.set_config(command="maxmemory", value=memory)
            else:
                redis_ins_status = False
                result['reason'] = "{0}实例运行状态异常请检查".format(redis_ins_name)
            if redis_ins_status:
                result['set_redis_mem'] = True
                obj.filter(running_ins_name=redis_ins_name).update(redis_ins_mem=memory)
                running_redis_obj.filter(running_ins_name=redis_ins_name).update(redis_ins_mem=memory)
                result['reason'] = "{0}实例运行扩缩容正常".format(redis_ins_name)
            else:
                result['set_redis_mem'] = False
            return Response(result)
        elif redis_type == "Redis-Sentinel":
            obj = RunningInsSentinel.objects.all()
            running_status_redis_obj = running_redis_obj.filter(running_ins_name=redis_ins_name).values('running_type')
            redis_ins_ip_port = obj.filter(running_ins_name=redis_ins_name).values("redis_ip", "running_ins_port",
                                                                                   "redis_type")
            serializer = RunningInsTimeSerializer(obj.filter(running_ins_name=redis_ins_name), many=True)
            result = serializer.data[0]
            if running_status_redis_obj[0]['running_type'] == "运行中":
                for ins_ip_port in redis_ins_ip_port:
                    if ins_ip_port["redis_type"] != "Redis-Sentinel":
                        redis_mon = RedisScheduled(redis_ip=ins_ip_port["redis_ip"],
                                                   redis_port=ins_ip_port["running_ins_port"])
                        redis_mon.set_config(command="maxmemory", value=memory)
            else:
                redis_ins_status = False
                result['reason'] = "{0}实例运行状态异常请检查".format(redis_ins_name)
            if redis_ins_status:
                result['set_redis_mem'] = True
                obj.filter(running_ins_name=redis_ins_name).update(redis_ins_mem=memory)
                running_redis_obj.filter(running_ins_name=redis_ins_name).update(redis_ins_mem=memory)
                result['reason'] = "{0}实例运行扩缩容正常".format(redis_ins_name)
            else:
                result['set_redis_mem'] = False
            return Response(result)
    except Exception as e:
        return Response("{0}实例扩缩容失败, 报错信息为{1}".format(redis_ins_name, e))