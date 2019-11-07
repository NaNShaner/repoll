from .models import models
from polls.models import *
import redis
from django.dispatch import receiver
from django.core.signals import request_finished
from django.forms.models import model_to_dict
import paramiko
import os
import subprocess
import logging
import time
from .tasks import mem_unit_chage
# 针对model 的signal
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save

# 定义信号
import django.dispatch
work_done = django.dispatch.Signal(providing_args=['redis_text', 'request'])


# def create_signal(request, redis_text):
#     print("我已经做完了工作。现在我发送一个信号出去，给那些指定的接收器。")
#
#     # 发送信号，将请求的url地址和时间一并传递过去
#     work_done.send(create_signal, request=request, redis_text=redis_text)
#     return HttpResponse("200,ok")
#
#
# @receiver(post_save, sender=ApplyRedisText, dispatch_uid="mymodel_post_save")
# def model_per_saved(sender, **kwargs):
#     redis_text = kwargs['instance'].apply_text
#     work_done.send(create_signal, redis_text=redis_text)
#
#
# @receiver(work_done, sender=create_signal)
# def my_callback(sender, **kwargs):
#     print("我在%s时间收到来自%s的信号" % (kwargs['redis_text'], sender))


@receiver(post_save, sender=ApplyRedisText, dispatch_uid="mymodel_post_save")
def my_model_handler(sender, **kwargs):
    redis_ip = ''
    redis_port = ''
    redis_apply_ip = Ipaddr.objects.all()
    redis_ins_id = kwargs['instance'].redis_ins_id
    redis_ins_obj = RedisIns.objects.filter(id=redis_ins_id)
    all_redis_ip = [redis_ip_ipaddr.__dict__['ip'] for redis_ip_ipaddr in redis_apply_ip]
    redis_text = kwargs['instance'].apply_text
    if isinstance(redis_text, str):
        try:
            redis_text_split = redis_text.split(":")
            redis_ip = redis_text_split[0]
            redis_port = redis_text_split[1]
            redis_mem = redis_text_split[2]
            if redis_ip not in all_redis_ip:
                print("{0}不在Redis云管列表中...".format(redis_ip))
                raise ValueError("{0}不在Redis云管列表中...".format(redis_ip))
        except ValueError as e:
            print(e)

    redis_ins_obj_type = redis_ins_obj.values('redis_type').first()
    redis_ins_obj_name = redis_ins_obj.values('redis_ins_name').first()
    redis_ins_obj_mem = redis_ins_obj.values('redis_mem').first()
    redis_ins_type = redis_ins_obj_type['redis_type']
    a = RedisStandalone(redis_ins=redis_ins_obj,
                        redis_ins_name=redis_ins_obj_name,
                        redis_ins_type=redis_ins_type,
                        redis_ins_mem=redis_ins_obj_mem,
                        redis_ip=redis_ip,
                        redis_port=redis_port)
    a.saved_redis_running_ins()
    if a.create_redis_conf_file():
        redis_start = RedisStartClass(host=redis_ip, redis_server_ctl="/opt/repoll/redis/src/redis-server " + "/opt/repoll/conf/" + str(redis_port) + ".conf &")
        if redis_start.start_server():
            print("Redis 启动成功，服务器IP：{0}, 启动端口为：{1}".format(redis_ip, redis_port))
        else:
            print("Redis 启动失败，服务器IP：{0}, 启动端口为：{1}".format(redis_ip, redis_port))


def get_redis_conf(redis_type):
    """
    通过redis的模式获取当前所有的配置文件
    :param redis_type:
    :return:
    """
    obj = RedisConf.objects.all().filter(redis_type=redis_type)
    return obj


def do_command(Host, commands):
    """
    Telnet远程登录：Windows客户端连接Linux服务器
    :param Host:
    :param commands:
    :return:
    """
    try:
        # 创建SSH对象
        ssh = paramiko.SSHClient()
        # 允许连接不在know_hosts文件中的主机
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 第一次登录的认证信息
        private_key = paramiko.RSAKey.from_private_key_file('/Users/bijingrui/.ssh/id_rsa')
        # 连接服务器
        ssh.connect(hostname=Host, port=22, username="root", pkey=private_key)
        # 执行命令
        stdin, stdout, stderr = ssh.exec_command(commands)

        # 获取命令结果
        res, err = stdout.read(), stderr.read()
        command_exit_result = res if res else err
        command_exit_status = stdout.channel.recv_exit_status()
        # 关闭连接
        ssh.close()

        return command_exit_status, command_exit_result
    except Exception as e:
        logging.info("{0}, ssh登陆失败，错误信息为{1}".format(Host, e))
    return False


def do_scp(Host, local_file, remote_file):
    """
    Telnet远程登录：Windows客户端连接Linux服务器
    :param Host:
    :param commands:
    :return:
    """
    try:
        # 创建SSH对象
        ssh = paramiko.SSHClient()
        # 允许连接不在know_hosts文件中的主机
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 第一次登录的认证信息
        private_key = paramiko.RSAKey.from_private_key_file('/Users/bijingrui/.ssh/id_rsa')
        # 连接服务器
        ssh.connect(hostname=Host, port=22, username="root", pkey=private_key)
        # 执行命令
        client = paramiko.Transport(Host)
        client.connect(username="root", pkey=private_key)
        sftp = paramiko.SFTPClient.from_transport(client)
        sftp.put(local_file, remote_file)
        client.close()
        return True
    except Exception as e:
        logging.info("{0}, ssh登陆失败，错误信息为{1}".format(Host, e))
    return False


def regx_redis_conf(key, value, port, maxmemory):
    if isinstance(key, str):
        try:
            if "_" in key:
                key = key.replace("_", "-")
                return key, value
            elif "%port%" in str(value):
                value = value.replace("%port%", port)
                return key, value
            elif "%dmb%" in str(value):
                value = value.replace("%dmb%", str(maxmemory) + "m")
                return key, value
            elif "%percentage%" in str(value):
                value = value.replace("%percentage%", "100%")
                return key, value
            elif "save900" in key:
                key = key.replace("save900", "save 900 ")
                return key, value
            elif "save300" in key:
                key = key.replace("save300", "save 900 ")
                return key, value
            elif "save60" in key:
                key = key.replace("save60", "save 900 ")
                return key, value
            elif "logfile" in key:
                value = value.replace("/opt/repoll/", "/opt/repoll/logs/{0}.log".format(port))
                return key, value
            elif "clientOutputBufferLimitNormal" in key:
                key = key.replace("clientOutputBufferLimitNormal", "client-output-buffer-limit normal")
                return key, value
            elif "clientOutputBufferLimitSlave" in key:
                key = key.replace("clientOutputBufferLimitSlave", "client-output-buffer-limit slave")
                return key, value
            elif "clientOutputBufferLimitPubsub" in key:
                key = key.replace("clientOutputBufferLimitPubsub", "client-output-buffer-limit pubsub")
                return key, value
            print(key, value)
        except ValueError as e:
            pass
    print(key, value)
    return key, value


class RedisStandalone:

    def __init__(self, redis_ins, redis_ins_name, redis_ins_type, redis_ins_mem, redis_ip, redis_port):
        self.redis_ins_ip = [r.__dict__ for r in redis_ins]
        self.redis_ins_name = redis_ins_name['redis_ins_name']
        self.redis_ins_type = redis_ins_type
        self.redis_ins_mem = redis_ins_mem['redis_mem']
        self.redis_ip = redis_ip
        self.redis_port = redis_port

    def standalone_conf(self):
        redis_conf = get_redis_conf(redis_type=self.redis_ins_type)
        return redis_conf

    def saved_redis_running_ins(self):
        obj = RunningInsTime(running_ins_name=self.redis_ins_name,
                             redis_type=self.redis_ins_type,
                             redis_ins_mem=self.redis_ins_mem,
                             redis_ip=self.redis_ip,
                             running_ins_port=self.redis_port
                             )
        obj.save()
        return True

    def create_redis_conf_file(self):
        redis_conf = get_redis_conf(self.redis_ins_type)
        all_redis_conf = [conf_k_v.__dict__ for conf_k_v in redis_conf]
        redis_dir = all_redis_conf[0]['dir']
        conf_file_name = "/Users/bijingrui/PycharmProjects/mysite1/templates/" + str(self.redis_port) + ".conf"
        with open(conf_file_name, 'w+') as f:
            for k, v in all_redis_conf[0].items():
                if k != 'id' and k != 'redis_version' and k != 'redis_type':
                    if isinstance(v, str) or isinstance(v, int):
                        k, v = regx_redis_conf(key=k, value=v, port=self.redis_port, maxmemory=mem_unit_chage(self.redis_ins_mem))
                        f.write(k + " " + str(v) + "\n")
        # print(do_telnet(self.redis_ip, "ls -trl /opt/"))
        if do_scp(self.redis_ip, conf_file_name, "/opt/repoll/conf/" + str(self.redis_port) + ".conf"):
            print("文件分发成功")
        else:
            print("文件分发失败")
            return False
        return True


# def log(log_type, msg=None, asset=None, new_asset=None, request=None):
#     """
#     记录日志
#     """
#     event = models.EventLog()
#     if log_type == "upline":
#         event.name = "%s <%s> ：  上线" % (asset.name, asset.sn)
#         event.asset = asset
#         event.detail = "资产成功上线！"
#         event.user = request.user
#     elif log_type == "approve_failed":
#         event.name = "%s <%s> ：  审批失败" % (new_asset.asset_type, new_asset.sn)
#         event.new_asset = new_asset
#         event.detail = "审批失败！\n%s" % msg
#         event.user = request.user
#     # 更多日志类型.....
#     event.save()


class RedisStartClass:

    def __init__(self, host, redis_server_ctl):
        self.redis_server_ctl = redis_server_ctl
        self.host = host

    def start_server(self):
        do_command_result = do_command(self.host, self.redis_server_ctl)
        print("haha = = {0}".format(do_command_result))
        if do_command_result:
            if do_command_result[0] == 0:
                return True
        else:
            return False


class ApproveRedis:
    """
    审批资产并上线。
    """
    def __init__(self, request, asset_id):
        self.request = request
        self.asset_id = asset_id
        self.new_asset = RedisApply.objects.get(id=asset_id)
        # self.data = json.loads(self.new_asset.data)

    # def asset_upline(self):
    #     # 为以后的其它类型资产扩展留下接口
    #     func = getattr(self, "asset_upline")
    #     ret = func()
    #     return ret

    def _server_upline(self):
        # 在实际的生产环境中，下面的操作应该是原子性的整体事务，任何一步出现异常，所有操作都要回滚。
        asset = self.create_asset()  # 创建一条资产并返回资产对象。注意要和待审批区的资产区分开。
        print(asset)
        return True

    def create_asset(self):
        """
        创建Redis实例并上线
        :return:
        """
        # 利用request.user自动获取当前管理人员的信息，作为审批人添加到Redis实例数据中。
        try:
            if not RedisIns.objects.filter(redis_ins_name=self.new_asset.apply_ins_name):
                asset = RedisIns.objects.create(redis_ins_name=self.new_asset.apply_ins_name,
                                                ins_disc=self.new_asset.ins_disc,
                                                redis_type=self.new_asset.redis_type,
                                                redis_mem=self.new_asset.redis_mem,
                                                sys_author=self.new_asset.sys_author,
                                                area=self.new_asset.area,
                                                pub_date=self.new_asset.pub_date,
                                                approval_user=self.request.user,
                                                ins_status=RedisIns.ins_choice[3][0]
                                                )
            else:
                return False
        except ValueError as e:
            return e
        return asset

    def deny_create(self):
        """

        :return:
        """
        try:
            if not RedisIns.objects.filter(redis_ins_name=self.new_asset.apply_ins_name):
                asset = RedisIns.objects.create(redis_ins_name=self.new_asset.apply_ins_name,
                                                ins_disc=self.new_asset.ins_disc,
                                                redis_type=self.new_asset.redis_type,
                                                redis_mem=self.new_asset.redis_mem,
                                                sys_author=self.new_asset.sys_author,
                                                area=self.new_asset.area,
                                                pub_date=self.new_asset.pub_date,
                                                approval_user=self.request.user,
                                                ins_status=RedisIns.ins_choice[3][0]
                                                )
                if RedisIns.objects.filter(redis_ins_name=self.new_asset.apply_ins_name).values('ins_status') == 0:
                    RedisApply.objects.filter(redis_ins_name=self.new_asset.apply_ins_name).update(
                        apply_status=RedisApply.status_choice[2][0]
                    )
            else:
                RedisIns.objects.filter(redis_ins_name=self.new_asset.apply_ins_name).update(ins_status=RedisIns.ins_choice[3][0])
                RedisApply.objects.filter(redis_ins_name=self.new_asset.apply_ins_name).update(
                    apply_status=RedisApply.status_choice[2][0]
                )
                return True
        except ValueError as e:
            return e
        return asset

    def redis_apply_status_update(self):
        RedisApply.objects.filter(id=self.asset_id).update(apply_status=1)
        # obj.save()
        return True







