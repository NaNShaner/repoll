from .models import RunningInsTime
from .handlers import RedisStartClass
# 序列化器，把数据包装成类似字典的格式
from rest_framework import serializers

# 这两个模块把序列化后的数据包装成 api
from rest_framework.response import Response
from rest_framework.decorators import api_view


# 创建一个 Book 的序列化器
class RunningInsTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RunningInsTime  # 序列化的对象
        # fields = '__all__'  # 序列化的属性
        # fields = ('title', 'author')  # 如果只需要序列化某几个属性可以用元组
        fields = ['running_ins_name', 'redis_type', 'redis_ip', 'running_ins_port', 'redis_ins_mem'] or '__all__'


@api_view(['GET'])
def RedisStop(request, ins_id):
    running_ins_time = RunningInsTime.objects.all() # Book 的全部数据
    running_ins = running_ins_time.filter(id=ins_id)
    running_ins_name = running_ins.values('running_ins_name').first()
    running_ins_ip = running_ins.values('redis_ip').first()
    running_ins_port = running_ins.values('running_ins_port').first()
    RedisIns = RedisStartClass(host=running_ins_ip['redis_ip'],
                               redis_server_ctl="/opt/repoll/redis/src/redis-cli -p {0} shutdown".format(running_ins_port['running_ins_port']))
    if RedisIns.start_server():
        serializer = RunningInsTimeSerializer(running_ins, many=True) # 序列化 Book 的数据
        print("Redis is down")
        return Response(serializer.data)
    return Response("{0} : Redis 实例停止失败".format(running_ins_name['running_ins_name']))
