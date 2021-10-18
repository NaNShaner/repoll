from django.core.exceptions import ValidationError
from django.utils.html import format_html
from IPy import IP
import itertools as it
import re
from django.db import connection
from django.conf import settings


def my_custom_sql():
    """
    链接数据库查询库中所有资源池的IP地址
    :return: 所有资源池IP地址
    :type: list
    """
    row_list = []
    cursor = connection.cursor()
    db_name = settings.DATABASES
    cursor.execute(f"SELECT ip FROM {db_name['default']['NAME']}.polls_ipaddr")
    row = cursor.fetchall()
    for i in row:
        row_list.append(i[0])
    return row_list


def judge_legal_ip(ip):
    """
    正则匹配方法,判断一个字符串是否是合法IP地址
    :param ip:
    :return:
    """
    compile_ip = re.compile('^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
    if compile_ip.match(ip):
        return True
    else:
        return False


def redis_apply_text(apply_text, redis_type=None):
    """
    解析审批页面中输入的文本信息，并格式化输出
    :param apply_text: 审批页面中输入的原始文本信息
    :param redis_type: redis的运行模式，目前支持Standalone和Sentinel
    :return: 返回格式化后的文本信息dict
    """
    return_text = "输入规则错误请遵循如下规则: </br>" \
                  "1. standalone类型：</br>" \
                  "masterIp:masterPort:memSize(M)(例如：10.10.xx.xx:2048)</br>" \
                  "2. sentinel类型：</br>" \
                  "masterIp:masterPort:memSize(M):masterName:slaveIp:slavePort</br>" \
                  "sentinelIp1</br>" \
                  "sentinelIp2</br>" \
                  "sentinelIp3" \
                  "3. Cluster类型（集群各实例端口不建议大于50000）: </br>" \
                  "master1Ip:master1Port:memSize(M):slave1Ip:slave1Port</br>" \
                  "master2Ip:master2Port:memSize(M):slave2Ip:slave2Port</br>" \
                  "master3Ip:master3Port:memSize(M):slave3Ip:slave3Port</br>"
    mysql_ip_row = my_custom_sql()
    if redis_type:
        if isinstance(apply_text, str) and redis_type == 'Redis-Standalone':
            redis_text_split = apply_text.split(":")
            try:
                if redis_text_split[0] not in mysql_ip_row:
                    raise ValidationError("服务器{0},不在资源池列表中".format(redis_text_split[0]))
                apply_text_dict = {
                    'redis_ip': redis_text_split[0],
                    'redis_port': redis_text_split[1],
                    'redis_mem': redis_text_split[2]
                }
            except Exception as e:
                raise ValidationError("文本格式输入错误，{0}".format(e))
            return apply_text_dict
        elif redis_type == 'Redis-Sentinel':
            try:
                all_line = apply_text.split('\r\n')
                redis_ins = all_line.pop(0)
                all_redis_ins = redis_ins.split(":")
                redis_mem = all_redis_ins.pop(2)
                redis_master_name = all_redis_ins.pop(2)
                all_redis_ins_ip = all_redis_ins[::2]
                all_redis_ins_port = all_redis_ins[1::2]
                redis_master_ip_port = {all_redis_ins_ip.pop(0): all_redis_ins_port.pop(0)}
                redis_slave_ip_port_list = []
                for i in all_redis_ins_ip:
                    if i not in mysql_ip_row:
                        raise ValidationError("服务器{0},不在资源池列表中或文本格式不正确".format(i))
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
            except Exception as e:
                # 报错前端不显示
                raise ValidationError("文本格式输入错误，{0}".format(e))
        elif redis_type == 'Redis-Cluster':
            redis_text_split = apply_text.split("\r\n")
            text_list = []
            for redis_ins in redis_text_split:
                text_dict = {}
                redis_inline = redis_ins.split(":")
                redis_mem = redis_inline.pop(2)
                try:
                    all_redis_ins_ip = redis_inline[::2]
                    for i in all_redis_ins_ip:
                        if i not in mysql_ip_row:
                            raise ValidationError("服务器{0},不在资源池列表中".format(i))
                    all_redis_ins_port = redis_inline[1::2]
                    all_redis = list(zip(all_redis_ins_ip, all_redis_ins_port))
                    text_dict["redis_ip_port"] = all_redis
                    text_dict['redis_mem'] = redis_mem
                    text_list.append(text_dict)
                except IndexError as e:
                    pass
            return text_list
        else:
            raise ValidationError("输入格式校验错误，请核对文本规则")
    else:
        redis_text_split = apply_text.split(":")
        if len(redis_text_split) < 2:
            raise ValidationError(format_html(return_text))
        else:
            if '\r\n' not in apply_text:
                if len(apply_text.split(":")) != 3:
                    raise ValidationError("单机格式文本校验错误")
                else:
                    redis_ip_check = apply_text.split(":")[0]
                    redis_port_check = apply_text.split(":")[1]
                    try:
                        IP(redis_ip_check)
                        if redis_ip_check not in mysql_ip_row:
                            raise ValidationError("服务器{0},不在资源池列表中".format(redis_ip_check))
                        int(redis_port_check)
                        if len(redis_ip_check.split(".")) != 4:
                            raise ValidationError("单机格式文本校验错误, 请确认输入的IP是{0}".format(redis_ip_check))
                    except Exception as e:
                        raise ValidationError("单机格式文本校验错误, 请确认输入文本{0}".format(e))
            elif '\r\n\r\n' in apply_text:
                raise ValidationError("审批文本中存在多余的空行，请删除空行")
            else:
                all_line = apply_text.split('\r\n')
                all_ip_list = []
                for one_line in all_line:
                    one_line_part = one_line.split(":")
                    try:
                        for part in one_line_part:
                            if judge_legal_ip(part):
                                all_ip_list.append(part)
                    except ValueError:
                        pass
                try:
                    for ip in all_ip_list:
                        IP(ip)
                        if ip not in mysql_ip_row:
                            raise ValidationError("服务器{0},不在资源池列表中".format(ip))
                except Exception as e:
                    raise ValidationError("文本输入格式错误，请检查并纠正错误{0}".format(e))


def split_integer(m, n):
    """
    正对redis cluster的slot等份划分
    :param m: 16384
    :param n: 等份的份数
    :return:
    """
    assert n > 0
    quotient = int(m / n)
    remainder = m % n
    if remainder > 0:
        return [quotient] * (n - remainder) + [quotient + 1] * remainder
    if remainder < 0:
        return [quotient - 1] * -remainder + [quotient] * (n + remainder)
    return [quotient] * n


def slot_split_part(n):
    """
    根据slot等分的份数，格式化redis命令行添加slot所需的格式
    :param n: split_integer函数的返回结果
    :return:
    """
    return ['..'.join((str(i + 1), str(j))) for i, j in zip([-1] + list(it.accumulate(n[:-1])), it.accumulate(n))]


def recreate_conf_file():
    """
    TODO：从平台外部导入的reids实例，获取配置文件的绝对路径
    :return:
    """
    pass
