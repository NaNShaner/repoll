# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from .models import RealTimeQps, RunningInsTime

# pyecharts
from jinja2 import Environment, FileSystemLoader
from pyecharts.globals import CurrentConfig
from django.http import HttpResponse
CurrentConfig.GLOBAL_ENV = Environment(loader=FileSystemLoader("./templates/polls"))
from pyecharts import options as opts
from pyecharts.charts import Line


# Create your views here.

# echarts
def redis_qps(request, ins_id):
    real_time_qps = RealTimeQps.objects.all()
    running_ins_time = RunningInsTime.objects.all()
    real_time_obj = real_time_qps.filter(redis_running_monitor_id=ins_id).order_by('-collect_date')[:60]
    running_ins = running_ins_time.filter(id=ins_id)
    running_ins_name = running_ins.values('running_ins_name').first()
    running_ins_ip = running_ins.values('redis_ip').first()
    running_ins_port = running_ins.values('running_ins_port').first()
    real_time = [real_time.__dict__['collect_date'] for real_time in real_time_obj]
    redis_qps = [redis_qps.__dict__['redis_qps'] for redis_qps in real_time_obj]
    c = (
        Line()
        .add_xaxis(real_time)
        .add_yaxis(running_ins_name['running_ins_name'], redis_qps, is_smooth=True)
        .set_global_opts(title_opts=opts.TitleOpts(title="{0}:{1}".format(running_ins_ip['redis_ip'],
                                                                          running_ins_port['running_ins_port']),
                                                   subtitle="Redis QPS图"),
                         toolbox_opts=opts.ToolboxOpts(),
                         datazoom_opts=[opts.DataZoomOpts(), opts.DataZoomOpts(type_="inside")],)
    )
    return HttpResponse(c.render_embed())


def favicon(request):
    img = "static/favicon.ico"
    image_date = open(img, "rb").read()
    return HttpResponse(image_date, content_type='image/jpg')

