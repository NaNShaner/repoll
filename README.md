<div align="center">
<img src="https://github.com/NaNShaner/repoll/blob/develop/images/R.png" width="350">
</div>

[![ice](https://img.shields.io/badge/developing%20with-Simpleui-2077ff.svg)](https://github.com/newpanjing/simpleui)
![](https://img.shields.io/badge/build-passing-green.svg)
![Django CI](https://github.com/NaNShaner/repoll/workflows/Django%20CI/badge.svg)
# repoll
使用django框架编写的redis的管理平台，[项目wiki](https://github.com/NaNShaner/repoll/wiki)
![Anurag's github stats](https://github-readme-stats.vercel.app/api?username=NaNShaner&show_icons=true&theme=radical)
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
# yum install mysql-devel python3-devel 
pip3 install -r requirements.txt
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

* 执行以下命令完成simpleui的静态资源离线可访问
```
cd /django/repoll
python3 manage.py  collectstatic
```
* 创建管理员用户
```bash
python3 manage.py createsuperuser #用户名密码，自定义
```
* 如需对接ldap请根据setting注释根据实际情况修改配置
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

# 初始化redis各模式的配置
```bash
python3 manage.py loaddata /django/repoll/init_data.json
```

# 初始化redis资源池服务器
* 在平台内点击资源池服务器列表，点击增加输入相关字段即可
![image](https://github.com/NaNShaner/repoll/blob/develop/images/ResourcePool.png?raw=true)
* 特别注意！！！
所有资源池中的服务器，安装redis必须使用平台提供的脚本完成安装，命令如下：
```bash
sh repoll-init.sh repoll # 密码自定义
```

# 标准化申请流程
* 分配普通用户权限（dev或者ops角色）
* 领导层进行审批（boss角色）
* 管理员（dba角色）进行配置上线

# demo演示
http://43.143.240.39/
admin/admin


# Todo list
- [x] 支持哨兵模式和集群模式
- [x] 监控独立展示，包括qps、内存使用率、客户端链接以及慢查询等
- [x] 支持在线扩缩容的申请、审批、配置生效流程
- [x] 支持Redis密码
- [x] 支持导入已存在的redis实例
- [ ] 支持不同Redis集群间的数据迁移、同步、校验等运管功能
- [ ] 支持web console，在线执行redis命令
- [ ] 支持容器化部署
- [ ] 支持Redis实例容器化部署

# 声明
该项目将长期维护，期望有对redis有平台化管理的朋友加入一起维护。
如果您觉得该项目对您有所帮助，欢迎star

# 致谢
开发工具由[Jetbrains](https://www.jetbrains.com/)赞助的Pycharm