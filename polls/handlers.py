from .models import *
import paramiko
import logging
from .scheduled import mem_unit_chage
from django.core.exceptions import ValidationError
# 针对model 的signal
from django.dispatch import receiver
from django.db.models.signals import post_save
from .tools import redis_apply_text, split_integer, slot_split_part
import os
import logging
import copy


# 定义信号
# import django.dispatch
# work_done = django.dispatch.Signal(providing_args=['redis_text', 'request'])

# 定义项目绝对路径
TEMPLATES_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 日志格式
logging.basicConfig(filename="repoll.log", filemode="a+",
                    format="%(asctime)s %(name)s: %(levelname)s: %(message)s", datefmt="%d-%M-%Y %H:%M:%S",
                    level=logging.INFO)


@receiver(post_save, sender=ApplyRedisText, dispatch_uid="mymodel_post_save")
def apply_redis_text_handler(sender, **kwargs):
    """
    触发器，前端页面在审批完后自动触发
    :param sender:
    :param kwargs:
    :return:
    """
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
                logging.info("Redis 单实例启动成功，服务器IP：{0}, 启动端口为：{1}".format(redis_ip, redis_port))
            else:
                logging.info("Redis 单实例启动失败，服务器IP：{0}, 启动端口为：{1}".format(redis_ip, redis_port))
                raise ValidationError("redis 单实例启动失败")
        else:
            raise ValidationError("redis 单实例启动失败")
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
        if create_sentinel_conf_file and create_master_slave_file:
            start_master = b.start_redis_master()
            if start_master:
                start_slave = b.start_slave_master()
                if start_slave:
                    b.start_sentinel_master()
                    logging.info("哨兵模式启动成功,redis_master_ip_port:{0},"
                                 "redis_slave_ip_port:{1},"
                                 "redis_sentinel_ip_port:{2},"
                                 "redis_master_name:{3}".format(redis_apply_text_split['redis_master_ip_port'],
                                                                redis_apply_text_split['redis_slave_ip_port'],
                                                                redis_apply_text_split['redis_sentinel_ip_port'],
                                                                redis_apply_text_split['redis_master_name']))
        else:
            raise ValidationError("redis 哨兵动失败")
        b.save_sentinel_redis_ins()
    elif redis_ins_type == 'Redis-Cluster':
        redis_list = []
        redis_cluster_mem_sum = 0
        for redis_one_ins in redis_apply_text_split:
            redis_one_ins_split = {"redis_master": redis_one_ins['redis_ip_port'][0],
                                   "redis_slave": redis_one_ins['redis_ip_port'][1:],
                                   "redis_mem": redis_one_ins['redis_mem']}
            redis_cluster_mem_sum += int(redis_one_ins['redis_mem'])
            redis_list.append(redis_one_ins_split)
        obj_runningins = RunningInsTime(running_ins_name=redis_ins_obj_name["redis_ins_name"],
                                        redis_type='Redis-Cluster',
                                        redis_ins_mem=redis_cluster_mem_sum,
                                        ins_status=0)
        obj_runningins.save()
        for redis_one_ins in redis_apply_text_split:
            for all_redis_ins in redis_one_ins['redis_ip_port']:
                if redis_one_ins['redis_ip_port'].index(all_redis_ins) == 0:
                    c = RedisClusterClass(redis_ins=redis_ins_obj,
                                          redis_ins_name=redis_ins_obj_name,
                                          redis_ins_type="Redis-Master",
                                          redis_ins_mem=redis_one_ins['redis_mem'],
                                          redis_ip=all_redis_ins[0],
                                          redis_port=all_redis_ins[1])
                    file_status = c.create_cluster_file()
                    if file_status:
                        c.start_all_redis_ins()
                        c.save_cluster_ins()
                    else:
                        raise ValidationError("redis cluster 启动失败")
                else:
                    c = RedisClusterClass(redis_ins=redis_ins_obj,
                                          redis_ins_name=redis_ins_obj_name,
                                          redis_ins_type="Redis-Slave",
                                          redis_ins_mem=redis_one_ins['redis_mem'],
                                          redis_ip=all_redis_ins[0],
                                          redis_port=all_redis_ins[1])
                    file_status = c.create_cluster_file()
                    if file_status:
                        c.start_all_redis_ins()
                        c.save_cluster_ins()
                    else:
                        raise ValidationError("redis cluster 启动失败")
        RedisIns.objects.filter(redis_ins_name=redis_ins_obj_name["redis_ins_name"]).update(on_line_status=0)
        start_cluster = StartRedisCluster(cluster_list=redis_list)
        redis_cluster_list = start_cluster.redis_cluster_list()
        start_cluster.redis_cluser_meet(redis_cluster_list)
        redis_cluster_node_info = start_cluster.get_cluster_info()
        if redis_cluster_node_info:
            start_cluster.add_slot_2_master(redis_cluster_node_info)
        else:
            logging.error("redis cluster 启动失败，集群信息为{0}".format(redis_list))
            raise ValidationError("redis cluster 启动失败")
    else:
        raise ValidationError("redis 模式错误")


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
    elif redis_type == 'Redis-Cluster':
        obj = RedisClusterConf.objects.all().filter()
    else:
        obj = None
    return obj


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
            elif "clusterconfigfile" in key:
                key = key.replace(key, "cluster-config-file")
                value = value.replace(value, "nodes-{0}.conf".format(kwargs['kwargs']['redis_port']))
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
        obj_runningins = RunningInsTime(running_ins_name=self.redis_ins_name,
                                        redis_type=self.redis_ins_type,
                                        redis_ins_mem=self.redis_ins_mem,
                                        # redis_ip=self.redis_ip,
                                        # running_ins_port=self.redis_port
                                        )
        obj_runningins.save()
        try:
            obj_runningins_now = RunningInsTime.objects.all().get(running_ins_name=self.redis_ins_name)
            obj = RunningInsStandalone(running_ins_name=self.redis_ins_name,
                                       redis_type=self.redis_ins_type,
                                       redis_ins_mem=self.redis_ins_mem,
                                       redis_ip=self.redis_ip,
                                       running_ins_port=self.redis_port,
                                       running_ins_id=obj_runningins_now.id
                                       )

            obj.save()
            RedisIns.objects.filter(redis_ins_name=self.redis_ins_name).update(on_line_status=0)
        except Exception:
            pass
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
            logging.info("文件分发成功")
        else:
            logging.error("文件分发失败")
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
        """
       启动redis的实例
        """
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
                    logging.info("文件分发成功")
                else:
                    logging.error("文件分发失败")
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
        """
        启动master实例
        """
        redis_master_start = RedisStartClass(host=self.redis_master_ip,
                                             redis_server_ctl="/opt/repoll/redis/src/redis-server /opt/repoll/conf/" +
                                             str(self.redis_master_port) + ".conf")
        start_result = redis_master_start.start_server()
        return start_result

    def start_slave_master(self):
        """
        启动slave实例
        """
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
        """
        启动哨兵实例
        """
        start_result_dict = {}
        for sentinel in self.redis_sentinel_ip_port:
            if isinstance(sentinel, str):
                redis_sentinel_ip, redis_sentinel_port = sentinel.split(":")
                redis_sentinel_start = RedisStartClass(host=redis_sentinel_ip,
                                                       redis_server_ctl="/opt/repoll/redis/src/redis-server /opt/repoll/conf/" +
                                                                        str(redis_sentinel_port) + "-sentienl.conf --sentinel")
                redis_sentinel_start_result = redis_sentinel_start.start_server()
                start_result_dict["{0}:{1}".format(redis_sentinel_ip, redis_sentinel_port)] = redis_sentinel_start_result
        return start_result_dict

    def save_sentinel_redis_ins(self):
        """
        配置入库
        """
        obj_runningins = RunningInsTime(running_ins_name=self.redis_ins_name['redis_ins_name'],
                                        redis_type=self.model_type,
                                        redis_ins_mem=self.redis_mem,
                                        )
        obj_runningins.save()
        all_redis_ip_port = []
        for slave_ip_port in self.redis_slave_ip_port:
            for slave_ip, slave_port in slave_ip_port.items():
                slave_ip_port_str = slave_ip + ":" + slave_port
                all_redis_ip_port.append(slave_ip_port_str)
        obj_runningins_now = RunningInsTime.objects.all().get(running_ins_name=self.redis_ins_name['redis_ins_name'])
        for redis_slave_ip_port in all_redis_ip_port:
            ip = redis_slave_ip_port.split(":")[0]
            port = redis_slave_ip_port.split(":")[1]
            obj = RunningInsSentinel(
                running_ins_name=self.redis_ins_name['redis_ins_name'],
                redis_type='Redis-Slave',
                running_ins_port=port,
                redis_ip=ip,
                redis_ins_mem=self.redis_mem,
                running_ins_standalone_id=obj_runningins_now.id,
            )
            obj.save()
        obj = RunningInsSentinel(
            running_ins_name=self.redis_ins_name['redis_ins_name'],
            redis_type='Redis-Master',
            running_ins_port=self.redis_master_port,
            redis_ip=self.redis_master_ip,
            redis_ins_mem=self.redis_mem,
            running_ins_standalone_id=obj_runningins_now.id,
        )
        obj.save()
        for sentinel_ip_port in self.redis_sentinel_ip_port:
            ip = sentinel_ip_port.split(":")[0]
            port = sentinel_ip_port.split(":")[1]
            obj_sentinel = RunningInsSentinel(
                running_ins_name=self.redis_ins_name['redis_ins_name'],
                redis_type=self.model_type,
                running_ins_port=port,
                redis_ip=ip,
                running_ins_standalone_id=obj_runningins_now.id,
            )
            obj_sentinel.save()
        RedisIns.objects.filter(redis_ins_name=self.redis_ins_name['redis_ins_name']).update(on_line_status=0)
        return True


class RedisClusterClass:

    def __init__(self, redis_ins, redis_ins_name, redis_ins_type, redis_ins_mem, redis_ip, redis_port):
        """
        单个redis的实例进行配置文件生成、配置文件分发、进程启动
        :param redis_ins:
        :param redis_ins_name:
        :param redis_ins_type:
        :param redis_ins_mem:
        :param redis_ip:
        :param redis_port:
        """
        self.redis_ins = [r.__dict__ for r in redis_ins]
        self.redis_ins_name = redis_ins_name['redis_ins_name']
        self.redis_ins_type = redis_ins_type
        self.redis_ins_mem = redis_ins_mem
        self.redis_ip = redis_ip
        self.redis_port = redis_port

    def create_cluster_file(self):
        """
        创建redis实例的配置文件，并分发到资源池服务器指定的目录下。分发文件支持ssh免密和用户密码校验
        使用用户密码校验目前是硬编码，后续优化支持读库
        :return:
        """
        redis_conf = get_redis_conf("Redis-Standalone")
        redis_cluster_conf = get_redis_conf("Redis-Cluster")
        all_redis_conf = [conf_k_v.__dict__ for conf_k_v in redis_conf]
        all_cluster_conf = [conf_k_v.__dict__ for conf_k_v in redis_cluster_conf]
        conf_file_name = "{0}/templates/".format(TEMPLATES_DIR) + str(self.redis_port) + "-cluser.conf"
        with open(conf_file_name, 'w+') as f:
            for k, v in all_redis_conf[0].items():
                if k != 'id' and k != 'redis_version' and k != 'redis_type':
                    if isinstance(v, str) or isinstance(v, int):
                        k, v = regx_redis_conf(key=k, value=v, port=self.redis_port,
                                               maxmemory=mem_unit_chage(self.redis_ins_mem))
                        f.write(k + " " + str(v) + "\n")
            for k, v in all_cluster_conf[0].items():
                if k != 'id' and k != 'redis_version' and k != 'redis_type':
                    if isinstance(v, str) or isinstance(v, int):
                        k, v = regx_redis_conf(key=k, value=v, port=self.redis_port,
                                               maxmemory=mem_unit_chage(self.redis_ins_mem),
                                               kwargs={"redis_port": self.redis_port})
                        f.write(k + " " + str(v) + "\n")
        if do_scp(self.redis_ip, conf_file_name, "/opt/repoll/conf/" + str(self.redis_port) + "-cluster.conf",
                  user_name="root", user_password="Pass@word"):
            logging.info("目标服务器{0}文件分发成功".format("/opt/repoll/conf/" + str(self.redis_port) + "-cluster.conf"))
        else:
            logging.error("目标服务器{0}文件分发失败".format("/opt/repoll/conf/" + str(self.redis_port) + "-cluster.conf"))
            return False
        return True

    def start_all_redis_ins(self):
        """
        启动所有redis实例
        :return:
        """
        redis_start = RedisStartClass(host=self.redis_ip,
                                      redis_server_ctl="/opt/repoll/redis/src/redis-server /opt/repoll/conf/" +
                                                       str(self.redis_port) + "-cluster.conf")
        if redis_start.start_server():
            logging.info("redis 实例{2}启动成功，ip:port: {0}:{1}".format(self.redis_ip, self.redis_port, self.redis_ins_name))
            return True
        else:
            logging.info("redis 实例{2}启动失败，ip:port: {0}:{1}".format(self.redis_ip, self.redis_port, self.redis_ins_name))
            return False

    def save_cluster_ins(self):
        """
        redis实例信息入库
        :return:
        """
        obj_runningins_now = RunningInsTime.objects.all().get(running_ins_name=self.redis_ins_name)
        obj = RunningInsCluster(
            running_ins_name=self.redis_ins_name,
            redis_type=self.redis_ins_type,
            running_ins_port=self.redis_port,
            redis_ip=self.redis_ip,
            redis_ins_mem=self.redis_ins_mem,
            running_ins_standalone=obj_runningins_now
        )
        obj.save()


class StartRedisCluster:

    def __init__(self, cluster_list):
        """
        启动Redis Cluster
        :param cluster_list: 所有redis实例的IP及PORT
        """
        if isinstance(cluster_list, list):
            self.cluster_list = cluster_list

    def redis_cluster_list(self):
        """
        格式化所有redis实例的IP及PORT
        :return: list
        """
        redis_list = []
        for redis_one_list in self.cluster_list:
            redis_list.append(redis_one_list['redis_master'])
            for redis_slave in redis_one_list['redis_slave']:
                redis_list.append(redis_slave)
        return redis_list

    def redis_cluser_meet(self, redis_ins_list):
        """
        redis集群内所有节点完成cluster meet
        :param redis_ins_list: 入参为格式化后的集群节点信息
        :return:
        """
        if isinstance(redis_ins_list, list):
            redis_ins_list_copy = copy.deepcopy(redis_ins_list)
            i = 0
            try:
                if i < len(redis_ins_list_copy):
                    i += 1
                    redis_ins_one = redis_ins_list_copy.pop(0)
                    redis_ins_list_copy.append(redis_ins_one)
                    redis_ins_one_ip = redis_ins_one[0]
                    redis_ins_one_port = redis_ins_one[1]
                    for redis_ins_one_by_one in redis_ins_list_copy:
                        redis_ins_one_by_one_ip = redis_ins_one_by_one[0]
                        redis_ins_one_port_port = redis_ins_one_by_one[1]
                        comm_line = "/opt/repoll/redis/src/redis-cli -c -h {0} -p {1} cluster meet {2} {3}".format(
                            redis_ins_one_ip, redis_ins_one_port, redis_ins_one_by_one_ip, redis_ins_one_port_port
                        )
                        _exex_command = do_command(host=redis_ins_one_ip, commands=comm_line, user_name="root", user_password="Pass@word")
                        if _exex_command[0] == 0:
                            logging.info("{0}:{1} cluster meet {2}:{3} is ok".format(
                                redis_ins_one_ip, redis_ins_one_port, redis_ins_one_by_one_ip, redis_ins_one_port_port))
                        else:
                            logging.info("{0}:{1} cluster meet {2}:{3} is fail, 报错信息为{4}".format(
                                redis_ins_one_ip, redis_ins_one_port, redis_ins_one_by_one_ip, redis_ins_one_port_port,
                                _exex_command[1]))
            except Exception as e:
                logging.error("Redis Cluster 启动失败，涉及节点为{0}，报错信息为{1}".format(self.cluster_list, e))

    def get_cluster_info(self):
        """
        获取cluster nodes信息，用于后续的主从关系添加
        :return: 所有节点的node id及ip对应关系
        """
        node_dict = {}
        redis_cluster_ip_port = self.cluster_list[0]
        _comm_line = "/opt/repoll/redis/src/redis-cli -c -h {0} -p {1} cluster nodes ".format(redis_cluster_ip_port['redis_master'][0], redis_cluster_ip_port['redis_master'][1])
        _comm_result = do_command(host=redis_cluster_ip_port['redis_master'][0], commands=_comm_line, user_name="root", user_password="Pass@word")
        if _comm_result[0] == 0:
            _comm_result_list = _comm_result[1].decode('unicode-escape')
            _comm_result_list = _comm_result_list.split("\n")
            node_dict = {one_line.split()[1]: one_line.split()[0] for one_line in _comm_result_list if one_line}
        if node_dict:
            return node_dict
        else:
            return None

    def add_slot_2_master(self, cluster_node_info):
        """
        给主节点添加slot，并完成主从节点关系
        :param cluster_node_info: 入参为所有节点的node id和ip对应关系
        :return:
        """
        # _slots = ["{0..5461}", "{5462..10922}", "{10923..16383}"]
        master_num = len(self.cluster_list)
        _slots = split_integer(16383, master_num)
        slot_split = slot_split_part(_slots)
        num = 0
        try:
            for redis_ip_port in self.cluster_list:
                redis_master_ip = redis_ip_port['redis_master']
                _add_slot_comm_line = "/opt/repoll/redis/src/redis-cli -c -h {0} -p {1} cluster addslots {2}{3}{4}"\
                    .format(redis_master_ip[0], redis_master_ip[1], "{", slot_split[num], "}")
                _ex_addslots_command = do_command(host=redis_master_ip[0],
                                                  commands=_add_slot_comm_line,
                                                  user_name="root",
                                                  user_password="Pass@word")
                if _ex_addslots_command[0] == 0:
                    logging.info("add slot 成功，命令行命令为{0}".format(_add_slot_comm_line))
                else:
                    logging.error("add slot 失败，报错为{0}".format(_ex_addslots_command[1]))
                for redis_slave_ip in redis_ip_port['redis_slave']:
                    _add_master_replca_comm_line = "/opt/repoll/redis/src/redis-cli -c -h {0} -p {1} cluster replicate {2}".format(
                        redis_slave_ip[0],
                        redis_slave_ip[1],
                        cluster_node_info['{0}:{1}'.format(redis_master_ip[0], redis_master_ip[1])]
                    )
                    logging.info(_add_master_replca_comm_line)
                    _ex_cluster_replicate = do_command(host=redis_slave_ip[0],
                                                       commands=_add_master_replca_comm_line,
                                                       user_name="root",
                                                       user_password="Pass@word")
                    if _ex_cluster_replicate[0] == 0:
                        logging.info("add replicate 成功")
                    else:
                        logging.error("add replicate 失败，报错为{0}".format(_ex_cluster_replicate[1]))
                num += 1
        except IOError as e:
            return False
        return True


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
                # RedisIns.objects.filter(redis_ins_name=self.new_asset.apply_ins_name).update(ins_status=RedisIns.ins_choice[3][0])
                # RedisApply.objects.filter(apply_ins_name=self.new_asset.apply_ins_name).update(
                #     apply_status=RedisApply.status_choice[2][0]
                # )
                # return True
                return False
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
