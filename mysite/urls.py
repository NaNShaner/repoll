"""mysite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.views import generic, static
from django.conf import settings

from django.contrib.auth.models import User
from rest_framework import serializers, viewsets, routers, permissions
from rest_framework.decorators import permission_classes
from polls.models import RunningInsTime
from polls.views import favicon
from polls.apis import import_ext_ins


# Serializers define the API representation.
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'password', 'email', 'is_staff']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        """
        使用rest_framework创建用户需要使用set_password对密码加密入库
        :param validated_data:
        :return:
        """
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            is_staff=validated_data['is_staff']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class RunningInsTimeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = RunningInsTime
        fields = ['running_ins_name', 'redis_type', 'redis_ins_mem', 'running_ins_used_mem_rate',
                  'running_time', 'ins_status']


@permission_classes((permissions.IsAdminUser, ))
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


@permission_classes((permissions.IsAdminUser, ))
class RunningInsTimeSet(viewsets.ModelViewSet):
    queryset = RunningInsTime.objects.all()
    serializer_class = RunningInsTimeSerializer


router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'redis_ins', RunningInsTimeSet)


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^polls/', include('polls.urls')),
    url(r'^$', generic.RedirectView.as_view(url='/admin/', permanent=False)),
    url(r'^apis/', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'favicon.ico$', favicon),
    url(r'^static/(?P<path>.*)$', static.serve,
        {'document_root': settings.STATIC_ROOT}, name='static'),
]
