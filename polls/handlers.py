from .models import *
from django.dispatch import receiver
import paramiko
import logging
from .tasks import mem_unit_chage
# 针对model 的signal
from django.dispatch import receiver
from django.db.models.signals import post_save

# 定义信号
import django.dispatch
work_done = django.dispatch.Signal(providing_args=['redis_text', 'request'])


@receiver(post_save, sender=ApplyRedisText, dispatch_uid="mymodel_post_save")
def apply_redis_text_handler(sender, **kwargs):
    """
    触发器，前端页面在完成审批后自动触发
    :param sender:
    :param kwargs:
    :return:
    """
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
        redis_start = RedisStartClass(host=redis_ip, redis_server_ctl="/opt/repoll/redis/src/redis-server " + "/opt/repoll/conf/" + str(redis_port) + ".conf")
        if redis_start.start_server():
            print("Redis 启动成功，服务器IP：{0}, 启动端口为：{1}".format(redis_ip, redis_port))
        else:
            print("Redis 启动失败，服务器IP：{0}, 启动端口为：{1}".format(redis_ip, redis_port))


@receiver(post_save, sender=ApplyRedisInfo, dispatch_uid="mymodel_post_save")
def apply_redis_info_handler(sender, **kwargs):
    redis_ins_id = kwargs['instance'].apply_ins_name
    redis_ins_obj = ApplyRedisInfo.objects.filter(apply_ins_name=redis_ins_id)

    redis_ins_obj_type = redis_ins_obj.values('redis_type').first()
    redis_ins_obj_name = redis_ins_obj.values('apply_ins_name').first()
    redis_ins_obj_mem = redis_ins_obj.values('redis_mem').first()
    ins_disc = redis_ins_obj.values('ins_disc').first()
    sys_author = redis_ins_obj.values('sys_author').first()
    pub_date = redis_ins_obj.values('pub_date').first()
    create_user = redis_ins_obj.values('create_user').first()
    apply_status = redis_ins_obj.values('apply_status').first()
    area = redis_ins_obj.values('area').first()
    obj = RedisApply(apply_ins_name=redis_ins_obj_name['apply_ins_name'],
                     ins_disc=ins_disc['ins_disc'],
                     redis_type=redis_ins_obj_type['redis_type'],
                     redis_mem=redis_ins_obj_mem['redis_mem'],
                     sys_author=sys_author['sys_author'],
                     area=area['area'],
                     pub_date=pub_date['pub_date'],
                     create_user=create_user['create_user'],
                     apply_status=apply_status['apply_status']
                     )
    obj.save()


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
    """
    对于redis的配置进行格式化，部分k，v需要进行替换
    :param key: redis.conf文件中的配置项
    :param value: redis.conf文件中的配置项的值
    :param port: Redis的端口
    :param maxmemory: Redis的最大内存
    :return:
    """
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
        except ValueError as e:
            pass
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
        if do_scp(self.redis_ip, conf_file_name, "/opt/repoll/conf/" + str(self.redis_port) + ".conf"):
            print("文件分发成功")
        else:
            print("文件分发失败")
            return False
        return True


class RedisStartClass:

    def __init__(self, host, redis_server_ctl):
        self.redis_server_ctl = redis_server_ctl
        self.host = host

    def start_server(self):
        do_command_result = do_command(self.host, self.redis_server_ctl)
        if do_command_result:
            if do_command_result[0] == 0:
                return True
        else:
            return False


class ApproveRedis:
    """
    审批Redis并写入待上线列表中。
    """
    def __init__(self, request, asset_id):
        self.request = request
        self.asset_id = asset_id
        self.new_asset = RedisApply.objects.get(id=asset_id)

    def create_asset(self):
        """
        创建Redis实例并上线，利用request.user自动获取当前管理人员的信息，作为审批人添加到Redis实例数据中。
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
            else:
                return False
        except ValueError as e:
            return e
        return asset

    def deny_create(self):
        """
        Redis审批拒绝，设置拒绝标志位
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
        """
        更新申请状态
        :return:
        """
        RedisApply.objects.filter(id=self.asset_id).update(apply_status=1)
        return True







