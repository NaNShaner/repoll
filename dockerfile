# 自定义镜像，底层使用官方Python运行时作为父镜像
FROM registry.cn-hangzhou.aliyuncs.com/repoll/mysite-repoll:0.3
 
# 设置工作目录为/app
WORKDIR /opt/repoll
 
# 将当前目录内容复制到位于/app中的容器中
COPY . /opt/repoll
 
# 安装requirements.txt中指定的任何所需包
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
 
# 定义环境变量
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

EXPOSE 8000

# 运行时容器提供的默认命令
CMD ["python", "/opt/repoll/manage.py runserver 0.0.0.0:8000"]
