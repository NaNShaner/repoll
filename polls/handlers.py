
from .models import models
from polls.models import RedisApply, RedisInfo, RedisIns
import redis

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
        创建资产并上线
        :return:
        """
        # 利用request.user自动获取当前管理人员的信息，作为审批人添加到资产数据中。
        try:
            if not RedisIns.objects.filter(ins_name=self.new_asset.ins_name):
                asset = RedisIns.objects.create(ins_name=self.new_asset.ins_name,
                                                ins_disc=self.new_asset.ins_disc,
                                                redis_type=self.new_asset.redis_type,
                                                redis_mem=self.new_asset.redis_mem,
                                                sys_author=self.new_asset.sys_author,
                                                area=self.new_asset.area,
                                                pub_date=self.new_asset.pub_date,
                                                approval_user=self.request.user,
                                                ins_status=RedisIns.ins_choice[0][0]
                                                )
            else:
                return False
        except ValueError as e:
            return e
        return asset

    def deny_create(self):
        """
        创建厂商
        :param asset:
        :return:
        """
        try:
            if not RedisIns.objects.filter(ins_name=self.new_asset.ins_name):
                asset = RedisIns.objects.create(ins_name=self.new_asset.ins_name,
                                                ins_disc=self.new_asset.ins_disc,
                                                redis_type=self.new_asset.redis_type,
                                                redis_mem=self.new_asset.redis_mem,
                                                sys_author=self.new_asset.sys_author,
                                                area=self.new_asset.area,
                                                pub_date=self.new_asset.pub_date,
                                                approval_user=self.request.user,
                                                ins_status=RedisIns.ins_choice[3][0]
                                                )
                if RedisIns.objects.filter(ins_name=self.new_asset.ins_name).values('ins_status') == 0:
                    RedisApply.objects.filter(ins_name=self.new_asset.ins_name).update(
                        apply_status=RedisApply.status_choice[2][0]
                    )
            else:
                RedisIns.objects.filter(ins_name=self.new_asset.ins_name).update(ins_status=RedisIns.ins_choice[3][0])
                RedisApply.objects.filter(ins_name=self.new_asset.ins_name).update(
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

    def redis_ping(self):
        r = redis.StrictRedis(host=self.new_asset.ins_name)
