
from django import forms
from .models import *

class Production(forms.Form):
    name = forms.CharField(max_length=50, label="名字")
    weight = forms.CharField(max_length=50, label="重量")
    size = forms.CharField(max_length=50, label="尺寸")
    choice_list = [
        (0, '华为'),
        (1, "苹果"),
        (2, "OPPO")
    ]
    type = forms.ChoiceField(choices=choice_list, label="型号")