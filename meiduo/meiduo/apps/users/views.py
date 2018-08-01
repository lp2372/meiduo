import random
import re
from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.views import APIView

from goods.models import SKU
from users import constants
from users.models import User
from rest_framework.response import Response
from users import serializers
from rest_framework.generics import GenericAPIView,CreateAPIView,RetrieveAPIView,UpdateAPIView
from rest_framework.mixins import UpdateModelMixin
from verifications.serializers import ImageCodeCheckSerializer
from .utils import get_user_by_account
# Create your views here.
from celery_task.sms.tasks import send_sms_code
from .constants import SMS_CODE_REDIS_EXPIRES,SEND_SMS_CODE_INTERVAL, USER_ADDRESS_COUNTS_LIMIT
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.mixins import CreateModelMixin,ListModelMixin
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
    """
       根据账号和图片验证码，获取发送短信的token
       """

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


# 请求方式： GET /sms_codes/?access_token=xxx
class SMSCodeByTokenView(APIView):
    """
   找回密码２　凭借token发送短信验证码
   """
    def get(self, request):
        # 验证access_token
        access_token = request.query_params.get("access_token")
        # 判断access是否存在
        if access_token is None:
            return Response({"message": "无妨问权限"}, status=status.HTTP_400_BAD_REQUEST)
        #验证access_token
        mobile = User.check_send_sms_code_token(access_token)
        if mobile is None:
            return Response({"message": "无效access_token"}, status=status.HTTP_400_BAD_REQUEST)
        # 判断是否在60s内
        redis_conn = get_redis_connection("verify_codes")

        send_flg = redis_conn.get("send_flag_%s" % mobile)

        if send_flg:
           return Response({'请求次数过于频繁'},status=status.HTTP_429_TOO_MANY_REQUESTS)
        # 生成短信验证码
        sms_code = "%04d" %random.randint(0,9999)
        # 保存短信验证码与发送记录
        pl = redis_conn.pipeline()
        pl.setex("sms_%s" % mobile,SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex("send_flag_%s" % mobile, SEND_SMS_CODE_INTERVAL, 1)
        pl.execute()
        #发布异步任务发送短信
        send_sms_code.delay(mobile,sms_code,SMS_CODE_REDIS_EXPIRES)

        return Response({"message": "OK"}, status.HTTP_200_OK)

 # GET accounts/(?P<account>\w{5,20})/password/token/?sms_code=xxx
class PasswordTokenView(GenericAPIView):
    """
    用户帐号设置密码的token
    """
    serializer_class = serializers.CheckSMSCodeSerializer

    def get(self,request,account):
        """
       根据用户帐号获取修改密码的token
       """
        serializer = self.get_serializer(data = request.query_params)
        serializer.is_valid(raise_exception = True)
        #获取序列化器中的user对象
        user = serializer.user
        # 生成 access_token
        access_token = user.generate_set_password_token()
        # 响应，返回access_token和user_id
        return Response({"user_id":user.id,"access_token":access_token})

# users/(?P<pk>\d+)/password/?access_token=xxx
class PasswordView(GenericAPIView,UpdateModelMixin):
    queryset = User.objects.all()
    serializer_class = serializers.ResetPasswordSerializer

    def post(self,request,pk):
        #　继承GenericAPIView,UpdateModelMixin，后直接调用父类已经写好业务逻辑self.update（）方法，
        # 我们只需要在序列化中实现序列化，反序列化，验证，保存数据方法
        return self.update(request, pk)

class UserDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.UserDetailSerializer

    def get_object(self):
        return self.request.user


class EmailView(UpdateAPIView):
    """
       保存用户邮箱
       """
    permission_classes = [IsAuthenticated]
    serializer_class =  serializers.EmailSerializer

    def get_object(self):
        return self.request.user

# GET /emails/verification/
class VerifyEmailView(APIView):
    """
      邮箱验证
      """
    def get(self,request):
        token = request.query_params.get("token")
        if not token:
            return Response({"message":"缺少token，无妨问权限"},status=status.HTTP_400_BAD_REQUEST)
        user = User.check_verify_email_token(token)
        if user is None:
            return Response({'message': '链接信息无效'}, status=status.HTTP_400_BAD_REQUEST)
        user.email_active  = True
        user.save()
        return Response({"message":"ok"},status=status.HTTP_200_OK)

class AddressViewSet(ModelViewSet):
    """
       用户地址新增与修改
       用户地址新增与修改
       """
    serializer_class = serializers.UserAddressSerializer

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted = False)

    def list(self, request, *args, **kwargs):
        """
           用户地址列表数据
           """
        queryset = self.get_queryset()

        serializer = self.get_serializer(queryset, many=True)
        user = request.user
        return Response({
            'user_id': user.id,
            'default_address_id': user.default_address_id, #数据库会自动增加＿id
            'limit': USER_ADDRESS_COUNTS_LIMIT,
            'addresses': serializer.data,})


    def create(self, request, *args, **kwargs):
        """
              保存用户地址数据
              """
        # 检查用户地址数据数目不能超过上限
        count = request.user.addresses.count()
        if count >= USER_ADDRESS_COUNTS_LIMIT:
            return Response({'message': '保存地址数据已达到上限'}, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)
    def destroy(self, request, *args, **kwargs):
        """
          处理删除
          """
        address = self.get_object()
        #逻辑删除
        address.is_deleted = True
        address.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    #　
    @action(methods=["put"],detail=True)
    def status(self,request,pk=None, address_id=None):

        address = self.get_object()
        request.user.default_address = address
        request.user.save()

        return Response({'message': 'OK'}, status=status.HTTP_200_OK)

    @action(methods=['put'],detail=True)
    def title(self, request, pk=None, address_id=None):
        """
               修改标题
               """
        address = self.get_object()
        serializer = serializers.AddressTitleSerializer(instance=address,data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class UserBrowsingHistoryView(GenericAPIView,CreateModelMixin,ListModelMixin):
    """
        用户浏览历史记录
        """
    serializer_class = serializers.AddUserBrowsingHistorySerializer
    permission_classes = [IsAuthenticated]

    def post(self,request):
        """
       保存
       """
        return self.create(request)

    def get(self,request):
        """
          获取
          """
        user_id = request.user.id
        redis_conn = get_redis_connection("history")
        history = redis_conn.lrange("history_%s" % user_id, 0, constants.USER_BROWSING_HISTORY_COUNTS_LIMIT - 1)
        skus = []
        for sku_id in history:
            sku_id = int(sku_id)
            sku = SKU.objects.get(id=sku_id)

            skus.append(sku)
        print(skus)
        s = serializers.SKUSerializer(skus,many=True) # 序列化查询集 many = True
        print(s.data)
        return Response(s.data)
