from .models import *
from django.dispatch import receiver
import paramiko
import logging
from .scheduled import mem_unit_chage
# 针对model 的signal
from django.dispatch import receiver
from django.db.models.signals import post_save
import os

# 定义信号
import django.dispatch
work_done = django.dispatch.Signal(providing_args=['redis_text', 'request'])

# 定义项目绝对路径
TEMPLATES_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@receiver(post_save, sender=ApplyRedisText, dispatch_uid="mymodel_post_save")
def apply_redis_text_handler(sender, **kwargs):
    """
    触发器，前端页面在审批完后自动触发
    :param sender:
    :param kwargs:
    :return:
    """
    redis_ip = ''
    redis_port = ''

    redis_ins_id = kwargs['instance'].redis_ins_id
    redis_ins_obj = RedisIns.objects.filter(id=redis_ins_id)
    redis_ins_type = redis_ins_obj.values('redis_type').first()['redis_type']
    redis_text = kwargs['instance'].apply_text
    redis_apply_text_split = redis_apply_text(redis_text, redis_type=redis_ins_type)
    redis_ins_obj_name = redis_ins_obj.values('redis_ins_name').first()
    redis_ins_obj_mem = redis_ins_obj.values('redis_mem').first()
    if redis_ins_type == 'Redis-Standalone':
        redis_ip = redis_apply_text_split['redis_ip']
        redis_port = redis_apply_text_split['redis_port']
        a = RedisStandalone(redis_ins=redis_ins_obj,
                            redis_ins_name=redis_ins_obj_name,
                            redis_ins_type=redis_ins_type,
                            redis_ins_mem=redis_apply_text_split['redis_mem'],
                            redis_ip=redis_ip,
                            redis_port=redis_port)
        a.saved_redis_running_ins()
        if a.create_redis_conf_file():
            redis_start = RedisStartClass(host=redis_ip,
                                          redis_server_ctl="/opt/repoll/redis/src/redis-server /opt/repoll/conf/" + str(redis_port) + ".conf")
            if redis_start.start_server():
                print("Redis 启动成功，服务器IP：{0}, 启动端口为：{1}".format(redis_ip, redis_port))
            else:
                print("Redis 启动失败，服务器IP：{0}, 启动端口为：{1}".format(redis_ip, redis_port))
    elif redis_ins_type == 'Redis-Sentinel':
        b = RedisModelStartClass(model_type='Redis-Sentinel',
                                 redis_ins=redis_ins_obj,
                                 redis_master_ip_port=redis_apply_text_split['redis_master_ip_port'],
                                 redis_slave_ip_port=redis_apply_text_split['redis_slave_ip_port'],
                                 redis_master_name=redis_apply_text_split['redis_master_name'],
                                 redis_sentinel_ip_port=redis_apply_text_split['redis_sentinel_ip_port'],
                                 redis_sentinel_num=redis_apply_text_split['redis_sentinel_num'],
                                 sentinel_down_after_milliseconds=30000,
                                 sentinel_failover_timeout=180000,
                                 sentinel_parallel_syncs=1,
                                 redis_mem=redis_apply_text_split['redis_mem'])
        create_sentinel_conf_file = b.create_sentienl_conf_file()
        create_master_slave_file = b.create_maser_slave_conf()
        print(create_sentinel_conf_file, create_master_slave_file)


@receiver(post_save, sender=ApplyRedisInfo, dispatch_uid="mymodel_post_save")
def apply_redis_info_handler(sender, **kwargs):
    """
    ApplyRedisInfo模型被保持时触发执行
    :param sender:
    :param kwargs:
    :return:
    """
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
    if redis_type == 'Redis-Standalone':
        obj = RedisConf.objects.all().filter(redis_type=redis_type)
    elif redis_type == 'Redis-Sentinel':
        obj = RedisSentienlConf.objects.all().filter()
    else:
        obj = None
    return obj


def redis_apply_text(apply_text, redis_type):
    """
    解析审批页面中输入的文本信息，并格式化输出
    :param apply_text: 审批页面中输入的原始文本信息
    :param redis_type: redis的运行模式，目前支持Standalone和Sentinel
    :return: 返回格式化后的文本信息dict
    """
    redis_apply_ip = Ipaddr.objects.all()
    all_redis_ip = [redis_ip_ipaddr.__dict__['ip'] for redis_ip_ipaddr in redis_apply_ip]
    try:
        if isinstance(apply_text, str) and redis_type == 'Redis-Standalone':
            redis_text_split = apply_text.split(":")
            apply_text_dict = {
                'redis_ip':  redis_text_split[0],
                'redis_port': redis_text_split[1],
                'redis_mem': redis_text_split[2]
            }
            if apply_text_dict['redis_ip'] not in all_redis_ip:
                print("{0}不在Redis云管列表中...".format(apply_text_dict['redis_ip']))
                raise ValueError("{0}不在Redis云管列表中...".format(apply_text_dict['redis_ip']))
            return apply_text_dict
        if redis_type == 'Redis-Sentinel':
            try:
                all_line = apply_text.split('\r\n')
                redis_ins = all_line.pop(0)
                all_redis_ins = redis_ins.split(":")
                redis_mem = all_redis_ins.pop(2)
                redis_master_name = all_redis_ins.pop(2)
                all_redis_ins_ip = all_redis_ins[::2]
                all_redis_ins_port = all_redis_ins[1::2]
                # all_redis_ins_ip_port = dict(zip(all_redis_ins_ip, all_redis_ins_port))
                redis_master_ip_port = {all_redis_ins_ip.pop(0): all_redis_ins_port.pop(0)}
                redis_slave_ip_port_list = []
                for i in all_redis_ins_ip:
                    for p in all_redis_ins_port:
                        redis_ins_ip_port_dict = {}
                        redis_ins_ip_port_dict[i] = p
                        if {i: p} not in redis_slave_ip_port_list:
                            redis_slave_ip_port_list.append(redis_ins_ip_port_dict)
                redis_sentinel = [redis_sentinel for redis_sentinel in all_line if redis_sentinel != '']
                apply_text_dict = {
                    'model_type': 'Redis-Sentinel',
                    'redis_master_ip_port': redis_master_ip_port,
                    'redis_master_name': redis_master_name,
                    'redis_sentinel_ip_port': redis_sentinel,
                    'redis_sentinel_num': len(redis_sentinel) - 1,
                    'redis_slave_ip_port': redis_slave_ip_port_list,
                    'redis_mem': redis_mem
                }
                return apply_text_dict
            except ValueError as e:
                pass
    except ValueError as e:
        print(e)


def do_command(host, commands, private_key_file=None, user_name=None, user_password=None):
    """
    登录远端服务器执行命令
    :param host: 远端主机
    :param commands:  到远端执行的命令
    :param user_name: 登录到远端的服务名
    :param private_key_file: 秘钥路径
    :param user_password: 用户密码
    :return:
    """
    try:
        # 创建SSH对象
        ssh = paramiko.SSHClient()
        # 允许连接不在know_hosts文件中的主机
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 第一次登录的认证信息
        if private_key_file:
            private_key = paramiko.RSAKey.from_private_key_file(private_key_file)
            # 连接服务器
            ssh.connect(hostname=host, port=22, username=user_name, pkey=private_key)
            # 执行命令
            stdin, stdout, stderr = ssh.exec_command(commands)
            # 获取命令结果
            res, err = stdout.read(), stderr.read()
            command_exit_result = res if res else err
            command_exit_status = stdout.channel.recv_exit_status()
            # 关闭连接
            ssh.close()
            return command_exit_status, command_exit_result
        else:
            # 连接服务器
            ssh.connect(hostname=host, port=22, username=user_name, password=user_password)
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
        logging.info("{0}, ssh登陆失败，错误信息为{1}".format(host, e))
    return False


def do_scp(host, local_file, remote_file, private_key_file=None, user_name=None, user_password=None):
    """
    拷贝redis的配置文件到指定的服务器中指定目录中
    :param host: 远端主机
    :param local_file:  本地redis的配置文件路径
    :param remote_file: 远端存放路径
    :param private_key_file: 秘钥路径
    :param user_password: 用户密码
    :param user_name: 用户名
    :return:
    """
    try:
        ssh = paramiko.SSHClient()
        # 允许连接不在know_hosts文件中的主机
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 第一次登录的认证信息
        if private_key_file:
            private_key = paramiko.RSAKey.from_private_key_file(private_key_file)
            # 连接服务器
            ssh.connect(hostname=host, port=22, username=user_name, pkey=private_key)
            # 执行命令
            client = paramiko.Transport(host)
            client.connect(username=user_name, pkey=private_key)
            sftp = paramiko.SFTPClient.from_transport(client)
            sftp.put(local_file, remote_file)
            client.close()
            return True
        else:
            # 连接服务器
            ssh.connect(hostname=host, port=22, username=user_name, password=user_password)
            # 执行命令
            client = paramiko.Transport(host)
            client.connect(username=user_name, password=user_password)
            sftp = paramiko.SFTPClient.from_transport(client)
            sftp.put(local_file, remote_file)
            client.close()
            return True
    except Exception as e:
        logging.info("{0}, ssh登陆失败，错误信息为{1}".format(host, e))
    return False


def regx_redis_conf(key, value, port, maxmemory=None, **kwargs):
    """
    对于redis的配置进行格式化，部分k，v需要进行替换
    :param key: redis.conf文件中的配置项
    :param value: redis.conf文件中的配置项的值
    :param port: Redis的端口
    :param maxmemory: Redis的最大内存
    :param kwargs: 需要修改的配置文件的kv
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
            elif "sentinelMonitor" in key:
                key = key.replace(key, "sentinel monitor ")
                value = value.replace("%masterName_ip_port_num%",
                                      " {0} {1} {2} {3}".format(kwargs['kwargs']['masterName'], kwargs['kwargs']['masterIp'],
                                                                kwargs['kwargs']['masterPort'], kwargs['kwargs']['sentienlNum']))
                return key, value
            elif "sentinelDownAfterMilliseconds" in key:
                key = key.replace(key, "sentinel down-after-milliseconds ")
                value = value.replace(value, " {0} 20000".format(kwargs['kwargs']['masterName']))
                return key, value
            elif "sentinelFailoverTimeout" in key:
                key = key.replace(key, "sentinel failover-timeout ")
                value = value.replace(value, " {0} 180000".format(kwargs['kwargs']['masterName']))
                return key, value
            elif "sentinelParallelSyncs" in key:
                key = key.replace(key, "sentinel parallel-syncs ")
                value = value.replace(value, " {0} 1".format(kwargs['kwargs']['masterName']))
                return key, value
        except ValueError as e:
            pass
    return key, value


class RedisStandalone:

    def __init__(self, redis_ins, redis_ins_name, redis_ins_type, redis_ins_mem, redis_ip, redis_port,
                 master_name=None, master_ip_port=None):
        """
        单个redis的实例进行配置文件生成、配置文件分发、进程启动
        :param redis_ins:
        :param redis_ins_name:
        :param redis_ins_type:
        :param redis_ins_mem:
        :param redis_ip:
        :param redis_port:
        :param master_name:
        :param master_ip_port:
        """
        self.redis_ins = [r.__dict__ for r in redis_ins]
        self.redis_ins_name = redis_ins_name['redis_ins_name']
        self.redis_ins_type = redis_ins_type
        self.redis_ins_mem = redis_ins_mem
        self.redis_ip = redis_ip
        self.redis_port = redis_port
        if master_name:
            self.master_name = master_name
            self.master_ip_port = master_ip_port
        else:
            self.master_name = None

    def standalone_conf(self):
        """
        获取Redis的standalone的所有配置项
        :return:
        """
        redis_conf = get_redis_conf(redis_type=self.redis_ins_type)
        return redis_conf

    def saved_redis_running_ins(self):
        """
        将上线实例写入数据库
        :return:
        """
        obj = RunningInsTime(running_ins_name=self.redis_ins_name,
                             redis_type=self.redis_ins_type,
                             redis_ins_mem=self.redis_ins_mem,
                             redis_ip=self.redis_ip,
                             running_ins_port=self.redis_port
                             )
        obj.save()
        return True

    def create_redis_conf_file(self):
        """
        创建redis实例的配置文件，并分发到资源池服务器指定的目录下。分发文件支持ssh免密和用户密码校验
        使用用户密码校验目前是硬编码，后续优化支持读库
        :return:
        """
        redis_conf = get_redis_conf(self.redis_ins_type)
        all_redis_conf = [conf_k_v.__dict__ for conf_k_v in redis_conf]
        redis_dir = all_redis_conf[0]['dir']
        conf_file_name = "{0}/templates/".format(TEMPLATES_DIR) + str(self.redis_port) + ".conf"
        with open(conf_file_name, 'w+') as f:
            for k, v in all_redis_conf[0].items():
                if k != 'id' and k != 'redis_version' and k != 'redis_type':
                    if isinstance(v, str) or isinstance(v, int):
                        k, v = regx_redis_conf(key=k, value=v, port=self.redis_port,
                                               maxmemory=mem_unit_chage(self.redis_ins_mem))
                        f.write(k + " " + str(v) + "\n")
            if self.master_name:
                _maser_ip_port = self.master_ip_port.split(":")
                f.write("slaveof {0} {1}".format(_maser_ip_port[0], _maser_ip_port[1]))
        if do_scp(self.redis_ip, conf_file_name, "/opt/repoll/conf/" + str(self.redis_port) + ".conf",
                  user_name="root", user_password="Pass@word"):
            print("文件分发成功")
        else:
            print("文件分发失败")
            return False
        return True


class RedisStartClass:

    def __init__(self, host, redis_server_ctl):
        """
        远程登录服务器，执行命令。包括Redis的起、停
        :param host:
        :param redis_server_ctl:
        """
        self.redis_server_ctl = redis_server_ctl
        self.host = host

    def start_server(self):
        do_command_result = do_command(self.host, self.redis_server_ctl, user_name="root", user_password="Pass@word")
        if do_command_result:
            if do_command_result[0] == 0:
                return True
        else:
            return False


class RedisModelStartClass:

    def __init__(self, model_type, redis_ins, redis_master_ip_port, redis_sentinel_ip_port, redis_slave_ip_port,
                 redis_master_name, redis_mem, redis_sentinel_num, sentinel_down_after_milliseconds=None,
                 sentinel_failover_timeout=None, sentinel_parallel_syncs=None):
        """
        非standalone模式的redis的实例配置文件生成、文件分发、实例启动
        :param model_type: 运行模式
        :param redis_ins: RedisIns 数据库qureySet
        :param redis_master_ip_port: 哨兵模式master的ip和port，输入数据类型str
        :param redis_sentinel_ip_port: 哨兵模式sentinel的ip和port，输入数据类型list
        :param redis_slave_ip_port: 哨兵模式slave的ip和port，输入数据类型list
        :param redis_master_name: 哨兵模式的mastername
        :param redis_mem: redis实例的最大内存
        :param redis_sentinel_num: 哨兵模式在多少个哨兵进行投票
        :param sentinel_down_after_milliseconds:
        :param sentinel_failover_timeout:
        :param sentinel_parallel_syncs:
        """
        self.model_type = model_type
        self.redis_ins = redis_ins
        redis_ins_query = [r.__dict__ for r in redis_ins]
        self.redis_ins_name = redis_ins_query[0]
        self.redis_master_name = redis_master_name
        self.redis_sentinel_ip_port = redis_sentinel_ip_port
        self.redis_slave_ip_port = redis_slave_ip_port
        self.redis_mem = redis_mem
        self.redis_sentinel_num = redis_sentinel_num
        if sentinel_down_after_milliseconds:
            self.sentinel_down_after_milliseconds = sentinel_down_after_milliseconds
        if sentinel_failover_timeout:
            self.sentinel_failover_timeout = sentinel_failover_timeout
        if sentinel_parallel_syncs:
            self.sentinel_parallel_syncs = sentinel_parallel_syncs
        if isinstance(redis_master_ip_port, dict) and len(redis_master_ip_port) == 1:
            for k, v in redis_master_ip_port.items():
                self.redis_master_ip = k
                self.redis_master_port = v

    def create_sentienl_conf_file(self):
        """
        创建redis 哨兵实例的配置文件，并分发到资源池服务器指定的目录下。分发文件支持ssh免密和用户密码校验
        使用用户密码校验目前是硬编码，后续优化支持读库
        :return:
        """
        redis_conf = get_redis_conf(self.model_type)
        all_redis_conf = [conf_k_v.__dict__ for conf_k_v in redis_conf]
        for sentinel in self.redis_sentinel_ip_port:
            if isinstance(sentinel, str):
                redis_sentinel_ip, redis_sentinel_port = sentinel.split(":")
                conf_file_name = "{0}/templates/".format(TEMPLATES_DIR) + str(redis_sentinel_port) + "-sentienl.conf"
                conf_modify = {
                    "masterName": self.redis_master_name,
                    "masterIp": self.redis_master_ip,
                    "masterPort": self.redis_master_port,
                    "sentienlNum": self.redis_sentinel_num,
                    # "sentinel_down_after_milliseconds": self.sentinel_down_after_milliseconds,
                    # "sentinel_failover_timeout": self.sentinel_failover_timeout,
                    # "sentinel_parallel_syncs": self.sentinel_parallel_syncs
                }
                with open(conf_file_name, 'w+') as f:
                    for k, v in all_redis_conf[0].items():
                        if k != 'id' and k != 'redis_type':
                            if isinstance(v, str) or isinstance(v, int):
                                k, v = regx_redis_conf(key=k, value=v,
                                                       port=redis_sentinel_port, kwargs=conf_modify)
                                f.write(k + " " + str(v) + "\n")
                if do_scp(redis_sentinel_ip, conf_file_name,
                          "/opt/repoll/conf/" + str(redis_sentinel_port) + "-sentienl.conf",
                          user_name="root", user_password="Pass@word"):
                    print("文件分发成功")
                else:
                    print("文件分发失败")
                    return False
        return True

    def create_maser_slave_conf(self):
        """
        创建master和slave的配置文件
        :return:
        """
        a = RedisStandalone(redis_ins=self.redis_ins,
                            redis_ins_name=self.redis_ins_name,
                            redis_ins_type='Redis-Standalone',
                            redis_ins_mem=self.redis_mem,
                            redis_ip=self.redis_master_ip,
                            redis_port=self.redis_master_port)
        a.create_redis_conf_file()

        for slave_ip_port in self.redis_slave_ip_port:
            for slave_ip, slave_port in slave_ip_port.items():
                a = RedisStandalone(redis_ins=self.redis_ins,
                                    redis_ins_name=self.redis_ins_name,
                                    redis_ins_type='Redis-Standalone',
                                    redis_ins_mem=self.redis_mem,
                                    redis_ip=slave_ip,
                                    redis_port=slave_port,
                                    master_name=self.redis_master_name,
                                    master_ip_port="{0}:{1}".format(self.redis_master_ip, self.redis_master_port))
                a.create_redis_conf_file()
        return True

    def start_redis_master(self):
        redis_master_start = RedisStartClass(host=self.redis_master_ip,
                                             redis_server_ctl="/opt/repoll/redis/src/redis-server /opt/repoll/conf/" +
                                             str(self.redis_master_port) + ".conf")
        start_result = redis_master_start.start_server()
        return start_result

    def start_slave_master(self):
        start_result_dict = {}
        for slave_ip_port in self.redis_slave_ip_port:
            for slave_ip, slave_port in slave_ip_port.items():
                redis_master_start = RedisStartClass(host=slave_ip,
                                                     redis_server_ctl="/opt/repoll/redis/src/redis-server /opt/repoll/conf/" +
                                                     str(slave_port) + ".conf")
                start_result = redis_master_start.start_server()
                start_result_dict["{0}:{1}".format(slave_ip, slave_port)] = start_result
        return start_result_dict

    def start_sentinel_master(self):
        start_result_dict = {}
        for sentinel in self.redis_sentinel_ip_port:
            if isinstance(sentinel, str):
                redis_sentinel_ip, redis_sentinel_port = sentinel.split(":")
                redis_sentinel_start = RedisStartClass(host=redis_sentinel_ip,
                                                       redis_server_ctl="/opt/repoll/redis/src/redis-server /opt/repoll/conf/" +
                                                                        str(redis_sentinel_port) + "-sentienl.conf --sentienl")
                start_result_dict["{0}:{1}".format(redis_sentinel_ip, redis_sentinel_port)] = redis_sentinel_start
        return start_result_dict


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
                RedisApply.objects.filter(apply_ins_name=self.new_asset.apply_ins_name).update(
                    apply_status=RedisApply.status_choice[2][0]
                )
                return True
        except ValueError as e:
            return e
        return asset

    def redis_apply_status_update(self, statu):
        """
        更新审批状态
        :param statu: 3为已审批， 4为已拒绝
        :return:
        """
        RedisApply.objects.filter(id=self.asset_id).update(apply_status=statu)
        ApplyRedisInfo.objects.filter(apply_ins_name=self.new_asset.apply_ins_name).update(apply_status=statu)
        return True

    @property
    def redis_ins_name(self):
        """
        返回redis实例名称
        :return:
        """
        return self.new_asset.apply_ins_name









