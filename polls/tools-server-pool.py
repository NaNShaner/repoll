from .models import Ipaddr, ServerUserPass


class ServerPool:

    def __init__(self, ip=None):
        if ip:
            self.ip = ip

    @property
    def server_pool_ip(self):
        """
        用于返回当前所有服务器ip地址
        :return:
        """
        all_server_obj = Ipaddr.objects.all()
        all_server_ip = all_server_obj.values_list("ip")
        return all_server_ip

    def server_user_passwd(self):
        """
        返回指定服务器的用户名及密码
        :return:
        """
        server_user_pass_obj = ServerUserPass.objects.all()
        server_user_pass = server_user_pass_obj.filter(server_ip=self.ip).values_list("user_name", "user_passwd")
        return server_user_pass

    @staticmethod
    def is_server_in_pool():
        """
        返回指定服务器是否在资源池中
        TODO:未完成实现
        :return:
        """
        all_server_ip = ServerPool.server_pool_ip

