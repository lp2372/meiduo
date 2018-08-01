from django.contrib.auth.models import AbstractUser
from django.db import models
from itsdangerous import TimedJSONWebSignatureSerializer, BadData
from django.conf import settings

from meiduo.utils.models import BaseModel
from . import constants
# Create your models here.
#创建自定义模型类,在Django认证系统的用户模型类上扩展字段
#继承Django提供了django.contrib.auth.models.AbstractUser用户抽象模型类
class User(AbstractUser):
    """用户模型类"""
    mobile = models.CharField(max_length=11,unique=True,verbose_name="手机号")
    email_active = models.BooleanField(default=False, verbose_name='邮箱验证状态')
    default_address = models.ForeignKey("Address",related_name="users",null=True,blank=True,on_delete=models.SET_NULL,verbose_name="默认地址")

    class Meta:
            db_table = "tb_user" #表名
            verbose_name = "用户"
            verbose_name_plural = verbose_name

    def generate_send_sms_code_token(self):
        """生成access_token"""
        # serializer = TimedJSONWebSignatureSerializer(密钥，有效期(s))
        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY,expires_in=constants.SEND_SMS_TOKEN_EXPIRES)
        #返回bytes类型
        token = serializer.dumps({'mobile':self.mobile})
        #byte ==> str
        token = token.decode()

        return token

    @staticmethod
    def check_send_sms_code_token(access_token):
        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY,expires_in=constants.SEND_SMS_TOKEN_EXPIRES)

        try:
            data = serializer.loads(access_token)
        except BadData:
            return None
        else:
            return data.get("mobile")

    def generate_set_password_token(self):
        """生成access_token"""
        # serializer = TimedJSONWebSignatureSerializer(密钥，有效期(s))
        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY,expires_in=constants.SEND_SMS_TOKEN_EXPIRES)
        #返回bytes类型
        token = serializer.dumps({'user_id':self.id})
        #byte ==> str
        token = token.decode()

        return token

    @staticmethod
    def check_set_password_token(access_token,user_id):
        """
       检验设置密码的token
       """
        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, expires_in=constants.SEND_SMS_TOKEN_EXPIRES)

        try:
            data = serializer.loads(access_token)
        except BadData:
            return None
        else:

            if user_id != str(data.get("user_id")):
                return False
            else:
                return True

    def generate_verify_email_token(self):
        """生成access_token"""
        # serializer = TimedJSONWebSignatureSerializer(密钥，有效期(s))
        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, expires_in=constants.SEND_SMS_TOKEN_EXPIRES)
        # 返回bytes类型
        token = serializer.dumps({'user_id': self.id,"email":self.email})
        # byte ==> str
        token = token.decode()
        return token
    @staticmethod
    def check_verify_email_token(token):

        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY,expires_in=constants.SEND_SMS_TOKEN_EXPIRES)
        try:
            data = serializer.loads(token)
        except BadData:
            return None
        else:
            email = data.get('email')
            user_id = data.get('user_id')
            try:
                user = User.objects.get(id= user_id,email=email)
            except User.DoseNotExist:
                return None
            else:
                return user


class Address(BaseModel):
    """
    用户地址
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses', verbose_name='用户')
    title = models.CharField(max_length=20, verbose_name='地址名称')
    receiver = models.CharField(max_length=20, verbose_name='收货人')
    province = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='province_addresses', verbose_name='省')
    city = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='city_addresses', verbose_name='市')
    district = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='district_addresses', verbose_name='区')
    place = models.CharField(max_length=50, verbose_name='地址')
    mobile = models.CharField(max_length=11, verbose_name='手机')
    tel = models.CharField(max_length=20, null=True, blank=True, default='', verbose_name='固定电话')
    email = models.CharField(max_length=30, null=True, blank=True, default='', verbose_name='电子邮箱')
    is_deleted = models.BooleanField(default=False, verbose_name='逻辑删除')

    class Meta:
        db_table = 'tb_address'
        verbose_name = '用户地址'
        verbose_name_plural = verbose_name
        ordering = ['-update_time']