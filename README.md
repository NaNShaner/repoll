# repoll
使用django框架编写的redis的管理平台

## 项目简介
### 主要功能（当前功能）
- Redis的申请、审批、配置上线
- Redis的监控、启动以及停止操作平台化管理
- 权限管理依赖django 框架
![image](https://github.com/NaNShaner/repoll/blob/master/images/main.png)

# 环境依赖
- 操作系统
```
Ubuntu 18.04
```
- 安装依赖
```
apt install python3-pip
apt-get install libmysqlclient-dev python3-dev
pip3 install -i http://pypi.douban.com/simple/ --trusted-host=pypi.douban.com  django==2.0
pip3 install -i http://pypi.douban.com/simple/ --trusted-host=pypi.douban.com  djangorestframework
pip3 install -i http://pypi.douban.com/simple/ --trusted-host=pypi.douban.com  django-crontab
pip3 install -i http://pypi.douban.com/simple/ --trusted-host=pypi.douban.com  mysqlclient
pip3 install -i http://pypi.douban.com/simple/ --trusted-host=pypi.douban.com  redis
pip3 install -i http://pypi.douban.com/simple/ --trusted-host=pypi.douban.com  paramiko
pip3 install -i http://pypi.douban.com/simple/ --trusted-host=pypi.douban.com  pyecharts==1.5.1
pip3 install -i http://pypi.douban.com/simple/ --trusted-host=pypi.douban.com  django-simpleui

```

# 配置Django
* 下载项目
```angular2html
make /django # 目录可以自定义
cd /django ; git clone https://github.com/NaNShaner/repoll.git
```
* 配置数据库链接
```
vi /django/repoll/mysite/settings.py
# 修改下文mysql的ip、port、库名、用户名以及密码
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django',
        'USER': 'root',
        'PASSWORD': 'Pass@word',
        'HOST': '127.0.0.1',
        'PORT': '32768',
    }
}
```

* 初始化数据库
```bash
python3 manage.py makemigrations
python3 manage.py migrate
```
* 数据库初始化完成后，去除上一步所配置的注释，再执行一次初始化数据库
* Django调试模式配置本级服务器IP
```bash
vi /django/repoll/mysite/settings.py


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [u'你本机的IP地址']
```
* 执行以下命令完成simpleui的静态资源离线可访问
```
cd /django/repoll
python3 manage.py  collectstatic
```
* 创建管理员用户
```bash
python3 manage.py createsuperuser #用户名密码，自定义
```
# 启动项目

* 开启redis的qps监控执行以下命令
```bash
cd /django/repoll
python3 manage.py crontab add
```
* 启动repoll
```bash
cd /django/repoll
python3 manage.py runserver 127.0.0.1:8000 # 这里的IP换成本机服务器IP，端口自定义
```
# 访问项目地址
```
http://127.0.0.1:8000/admin
```

# 标准化申请流程
* 分配普通用户权限（dev或者ops角色）
* 领导层进行审批（boss角色）
* 管理员（dba角色）进行配置上线

# Todo list
- [x] 支持哨兵模式和集群模式
- [ ] 监控独立展示，包括qps、内存使用率、客户端链接以及慢查询等
- [ ] 支持web console

# 声明
该项目将长期维护，期望有对redis有平台化管理的朋友加入一起维护。
