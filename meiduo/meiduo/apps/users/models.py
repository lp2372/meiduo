from django.contrib.auth.models import AbstractUser
from django.db import models
from itsdangerous import TimedJSONWebSignatureSerializer
from django.conf import settings
from . import constants
# Create your models here.
#创建自定义模型类,在Django认证系统的用户模型类上扩展字段
#继承Django提供了django.contrib.auth.models.AbstractUser用户抽象模型类
class User(AbstractUser):
    """用户模型类"""
    mobile = models.CharField(max_length=11,unique=True,verbose_name="手机号")

    class Meta:
        db_table = "tb_user" #表名
        verbose_name = "用户"
        verbose_name_plural = verbose_name

    def generate_send_sms_code_token(self):

        # serializer = TimedJSONWebSignatureSerializer(密钥，有效期(s))
        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY,expires_in=constants.SEND_SMS_TOKEN_EXPIRES)
        #返回bytes类型
        token = serializer.dumps({'mobile':self.mobile})
        #byte ==> str
        token = token.decode()

        return token
