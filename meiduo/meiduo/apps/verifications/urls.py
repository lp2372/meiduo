from django.conf.urls import url, include
from django.contrib import admin

from . import views

urlpatterns = [

    url(r'image_codes/(?P<image_code_id>.+)/$',views.ImageCodeView.as_view()),
    url(r'sms_codes/(?P<mobile>\d+)/$',views.SMSCodeView.as_view()),

]