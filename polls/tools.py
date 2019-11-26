from django.core.exceptions import ValidationError
# from .models import Ipaddr
from django.utils.html import format_html
from IPy import IP


def redis_apply_text(apply_text, redis_type=None):
    """
    解析审批页面中输入的文本信息，并格式化输出
    :param apply_text: 审批页面中输入的原始文本信息
    :param redis_type: redis的运行模式，目前支持Standalone和Sentinel
    :return: 返回格式化后的文本信息dict
    """
    # redis_apply_ip = Ipaddr.objects.all()
    # all_redis_ip = [redis_ip_ipaddr.__dict__['ip'] for redis_ip_ipaddr in redis_apply_ip]
    return_text = "输入规则错误请遵循如下规则: </br>" \
                  "1. standalone类型：</br>" \
                  "masterIp:masterPort:memSize(M)(例如：10.10.xx.xx:2048)</br>" \
                  "2. sentinel类型：</br>" \
                  "masterIp:masterPort:memSize(M):masterName:slaveIp:slavePort</br>" \
                  "sentinelIp1</br>" \
                  "sentinelIp2</br>" \
                  "sentinelIp3"
    if redis_type:
        redis_type = 'Redis-Standalone'
        if isinstance(apply_text, str) and redis_type == 'Redis-Standalone':
            redis_text_split = apply_text.split(":")
            try:
                apply_text_dict = {
                    'redis_ip':  redis_text_split[0],
                    'redis_port': redis_text_split[1],
                    'redis_mem': redis_text_split[2]
                }
            except Exception as e:
                raise ValidationError("文本格式输入错误，{0}".format(e))
            # if apply_text_dict['redis_ip'] not in all_redis_ip:
            #     raise ValidationError("{0}不在Redis云管列表中...".format(apply_text_dict['redis_ip']))
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
            except Exception as e:
                raise ValidationError("文本格式输入错误，{0}".format(e))
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
                        ip_check = IP(redis_ip_check)
                        port_check = int(redis_port_check)
                    except Exception as e:
                        raise ValidationError("单机格式文本校验错误, 请确认输入文本{0}".format(e))
            else:
                all_line = apply_text.split('\r\n')
                redis_ins = all_line.pop(0)
                all_redis_ins = redis_ins.split(":")
                redis_mem = all_redis_ins.pop(2)
                redis_master_name = all_redis_ins.pop(2)
                all_redis_ins_ip = all_redis_ins[::2]
                all_redis_ins_port = all_redis_ins[1::2]
                redis_sentinel = [redis_sentinel for redis_sentinel in all_line if redis_sentinel != '']
                try:
                    all_redis_ip = all_redis_ins_ip + redis_sentinel
                    for ip in all_redis_ip:
                        ip_check = IP(ip)
                    for port in all_redis_ins_port:
                        port_check = int(port)
                except Exception as e:
                    raise ValidationError("文本输入格式错误，请检查是否为哨兵模式，纠正错误{0}".format(e))
        # raise ValidationError(format_html(return_text))
