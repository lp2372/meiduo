import random

from django.shortcuts import render
from rest_framework import status

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from meiduo.libs.captcha.captcha import captcha
from .constants import IMAGE_CODE_REDIS_EXPIRES,SMS_CODE_REDIS_EXPIRES,SEND_SMS_CODE_INTERVAL
from django_redis import get_redis_connection
from django.http import HttpResponse
from meiduo.libs.yuntongxun.sms import CCP
from . import serializers
from celery_task.sms.tasks import send_sms_code
# Create your views here.

#图片验证码　GET /image_code/{image_code_id}/
#请求参数 image_code_id (uuid字符串,图片验证码编号)
class ImageCodeView(APIView):

    def get(self,request,image_code_id):
        #调用lib中第三方模块生成验证码
        text,image= captcha.generate_captcha()
        #存入redis
        redis_conn = get_redis_connection("verify_codes")
        # setex(key,time,value)
        redis_conn.setex("img_%s" %image_code_id,IMAGE_CODE_REDIS_EXPIRES,text)
        #返回图片二进制数据，需指定类型images/jpg
        return HttpResponse(image,content_type="images/jpg")

#短信验证码　后端接口　GET /sms_code/{mobile}/?image_code_id=xxx&text=xxx
class SMSCodeView(GenericAPIView):
    """短信验证码"""
    serializer_class = serializers.ImageCodeCheckSerializer


    def get(self,request,mobile):
        """创建短信验证码"""
        #判断验证码是否正确，判断是否在60s内
        serializer = self.get_serializer(data = request.query_params)
        serializer.is_valid(raise_exception =True)

        sms_code = "%04d" % random.randint(0, 9999)
        print(mobile,sms_code)
        #保存sms_code　以及发送记录
        redis_conn = get_redis_connection("verify_codes")
        p1 = redis_conn.pipeline() #获取redis管道对象，同样能执行redis操作名令
        #保存短信在redis中
        p1.setex("sms_%s" %mobile,SMS_CODE_REDIS_EXPIRES,sms_code)
        #保存短信发送标志在redis中
        p1.setex("send_flag_%s" % mobile,SEND_SMS_CODE_INTERVAL, 1)
        p1.execute()

        #发布celery异步任务
        send_sms_code.delay(mobile,sms_code,SMS_CODE_REDIS_EXPIRES)

        # #发送短信
        # ccp = CCP()
        # sms_code_expires = str(SMS_CODE_REDIS_EXPIRES/60)
        # # 注意： 测试的短信模板编号为1
        # sms_code = str(sms_code)
        # ccp.send_template_sms(mobile, [sms_code, sms_code_expires], 1)

        return Response({"message":"ok"},status=status.HTTP_200_OK)


