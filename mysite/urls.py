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


from django.contrib.auth.models import User
from rest_framework import serializers, viewsets, routers
from polls.models import Question, RedisInfo
from polls.views import homepage, showpost, favicon


# Serializers define the API representation.
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'password', 'email', 'is_staff']


class QuestionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Question
        fields = ['question_text', 'pub_date']


class RedisSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = RedisInfo
        fields = ['sys_type', 'redis_type', 'host_ip', 'redis_port', 'pub_date'] or "__all__"


# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer


class RedisViewSet(viewsets.ModelViewSet):
    queryset = RedisInfo.objects.all()
    serializer_class = RedisSerializer


router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'polls_question', QuestionViewSet)
router.register(r'redis', RedisViewSet)


urlpatterns = [
    url(r'^$', homepage),
    url(r'^admin/', admin.site.urls),
    url(r'^polls/', include('polls.urls')),
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^polls/(\w+)$', showpost),
    url(r'favicon.ico$', favicon)
]
