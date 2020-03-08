from django import forms
from .tools import redis_apply_text
from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import FormActions
from crispy_forms.layout import Layout, Submit, Row, Column, HTML


class NameForm(forms.Form):
    redis_ins_name = forms.CharField(label='应用名称', max_length=100)
    ins_disc = forms.CharField(label='应用描述', max_length=100)
    type_choice = [
        ("Redis-Standalone", "Redis-Standalone"),
        ("Redis-Cluster", "Redis-Cluster"),
        ("Redis-Sentinel", "Redis-Sentinel")
    ]
    redis_version = forms.CharField(label='Redis 版本', max_length=150, initial="3.0.6")
    redis_type = forms.ChoiceField(choices=type_choice, label="存储种类")
    redis_mem = forms.CharField(max_length=50, help_text="例如填写：512M,1G,2G..32G等", label="内存总量")
    sys_author = forms.CharField(max_length=50, label="项目负责人")
    area = forms.CharField(max_length=50, label="机房")
    apply_text = forms.CharField(label="实例详情", max_length=250,widget=forms.Textarea,
                                 help_text="具体规则如下: </br>"
                                           "1. standalone类型：</br>"
                                           "masterIp:masterPort:memSize(M)(例如：10.10.xx.xx:2048)</br>"
                                           "2. sentinel类型：</br>"
                                           "masterIp:masterPort:memSize(M):masterName:slaveIp:slavePort</br>"
                                           "sentinelIp1:sentinelPort1</br>"
                                           "sentinelIp2:sentinelPort2</br>"
                                           "sentinelIp3:sentinelPort3</br>"
                                           "3. Cluster类型:（集群各实例端口不建议大于50000）</br>"
                                           "master1Ip:master1Port:memSize(M):slave1Ip:slave1Port</br>"
                                           "master2Ip:master2Port:memSize(M):slave2Ip:slave2Port</br>"
                                           "master3Ip:master3Port:memSize(M):slave3Ip:slave3Port</br>",
                                 validators=[redis_apply_text])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'redis_ins_name',
            'redis_version',
            Row(
                Column('redis_mem', css_class='form-group col-md-6 mb-0'),
                Column('area', css_class='form-group col-md-6 mb-0'),
                # css_class='form-row'
            ),
            Row(
                Column('sys_author', css_class='form-group col-md-6 mb-0'),
                Column('redis_type', css_class='form-group col-md-6 mb-0'),
                # css_class='form-row'
            ),
            Row(
                Column('apply_text', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            FormActions(
                Submit('save', '提交'),
                HTML('<a href="/admin/polls/runninginstime/">'
                     '<input class=\'btn btn-default\' type=\'button\' value=\'取消\'/></a>'),
            )

        )
