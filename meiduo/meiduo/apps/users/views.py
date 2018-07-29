import re
from django.shortcuts import render
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from users.models import User
from rest_framework.response import Response
from users import serializers
from rest_framework.generics import GenericAPIView
from verifications.serializers import ImageCodeCheckSerializer
from .utils import get_user_by_account
# Create your views here.


class UsernameCountView(APIView):
    """
       用户名数量,验证注册的用户名是否已经存在
       """
    def get(self,request,username):

        count = User.objects.filter(username = username).count()

        return Response({"username:":username,"count":count})

class MobileCountView(APIView):
    """
    手机号数量,验证注册的手机号是否已经存在
    """
    def get(self,request,mobile):
        count = User.objects.filter(mobile=mobile).count()

        return Response({"mobile":mobile,"count":count})

class UserView(CreateAPIView):
    """
     用户注册
     """
    serializer_class =serializers.CreateUserSerializer

class SMSCodeTokenView(GenericAPIView):

    serializer_class = ImageCodeCheckSerializer

    def get(self,request,account):
        #验证图片验证码
        serializer = self.get_serializer(data = request.query_params)
        serializer.is_valid(raise_exception = True)

        user = get_user_by_account(account)
        if user is None:
            return Response({"message":"用户部不存在"},status=status.HTTP_404_NOT_FOUND)

        # 生成发送短信的access_token
        access_token = user.generate_send_sms_code_token()
        #保密手机号
        mobile = re.sub(r"(\d{3})(\d{4})(\d{4})",r"\1****\2",user.mobile)

        return Response({
            "mobile":mobile,"access_token":access_token
        })