from django.conf.urls import url
from . import views

app_name = 'rtmap'

urlpatterns = [
        url(r'^$', views.index),
        url(r'^map', views.map_view),
        ]
