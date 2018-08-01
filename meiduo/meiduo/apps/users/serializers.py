import re

from django_redis import get_redis_connection
from rest_framework import serializers

from goods.models import SKU
from users import constants
from users.models import User, Address
from rest_framework_jwt.settings import api_settings #引入jwt
from .utils import get_user_by_account
from django.core.mail import send_mail
from django.conf import settings
from celery_task.email.tasks import send_verify_email
class CreateUserSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(label="确认密码",max_length=20,min_length=8,write_only=True)
    allow = serializers.CharField(label='同意协议',write_only=True)
    sms_code = serializers.CharField(label='短信验证码',max_length=4,min_length=4,write_only=True)
    #需要添加此字段
    token = serializers.CharField(label='TOKEN令牌',max_length=200,min_length=4, read_only=True)

    def validate_mobile(self,value):
        """验证手机号"""
        if not re.match(r"^\d{11}$",value):
            raise serializers.ValidationError("手机格式错误")
        return value
    def validate_allow(self,value):
        """检验用户是否同意协议"""
        print(value)
        if value != 'true':
            raise serializers.ValidationError("请同意用户协议")
        return value
    def validate(self, attrs):
        mobile = attrs["mobile"]
        # 判断两次密码
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError('两次密码不一致')
        #判断短信验证码
        redis_conn = get_redis_connection("verify_codes")
        real_sms_code = redis_conn.get('sms_%s' % mobile)
        if real_sms_code is None:
            raise serializers.ValidationError('无效的短信验证码')
        if attrs["sms_code"] != real_sms_code.decode():
            raise serializers.ValidationError('短信验证码错误')
        return attrs

    def create(self, validated_data):
        del validated_data["password2"]
        del validated_data["sms_code"]
        del validated_data["allow"]
        #调用父类的create
        user = super().create(validated_data)
        # 调用django的认证系统加密密码
        user.set_password(validated_data["password"])
        user.save()

        #补充生成记录登录状态的token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        print(token)
        user.token = token #　token字段需要在序列化器中定义

        return user

    class Meta:
        model = User
        # 需要添token(jwt)字段
        fields = ("id","mobile","username","password","password2",'sms_code', 'mobile', 'allow','token')
        extract_kwargs = {
            "id":{"read_only":True},
            "username":{"max_length":20,"min_length":5,
                    'error_messages': {
                        'min_length': '仅允许5-20个字符的用户名',
                        'max_length': '仅允许5-20个字符的用户名',
                }},
            "password":{"write_only":True,'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }},

        }

class CheckSMSCodeSerializer(serializers.Serializer):
    """校验短信验证码和账号名的序列化"""
    sms_code = serializers.CharField(label="短信验证码",min_length=4,max_length=4)

    def validate(self, attrs):
        sms_code = attrs['sms_code']
        # 根据用户名获取用户模型对象
        account = self.context['view'].kwargs.get("account")
        user = get_user_by_account(account)
        if user is None:
            raise serializers.ValidationError("用户不存在")
        #验证短信验证码
        redis_conn = get_redis_connection('verify_codes')
        real_sms_code = redis_conn.get('sms_%s' % user.mobile)
        if real_sms_code is None:
            raise serializers.ValidationError("无效短信验证码")
        if sms_code != real_sms_code.decode():
            raise serializers.ValidationError("短信验证码错误")
        # 把当前对象作为序列化器的属性传递给视图中序列化对象
        self.user = user
        return attrs


class ResetPasswordSerializer(serializers.ModelSerializer):
    """
     重置密码序列化器
     """

    password2 = serializers.CharField(label='确认密码',write_only=True)
    access_token = serializers.CharField(label="操作token",write_only=True)

    class Meta:
        model = User
        fields = ("id","password","password2","access_token")
        extra_kwargs = {
            'password': {
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            }
        }

    def validate(self, attrs):
        """校验数据"""
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError("两次密码不一致")
        # 判断access token
        allow = User.check_set_password_token(attrs["access_token"],self.context['view'].kwargs.get("pk"))

        if not allow:
            raise serializers.ValidationError('无效的access token')
        return attrs
    def update(self, instance, validated_data):
        instance.set_password(validated_data["password"])
        instance.save()
        return instance


class UserDetailSerializer(serializers.ModelSerializer):
    """
    用户详情
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'mobile', 'email', 'email_active')


class EmailSerializer(serializers.ModelSerializer):
    """
       邮箱序列化器
       """
    def update(self, instance, validated_data):
        instance.email = validated_data["email"]
        instance.save()
        # 生成附带token的激活链接
        token = instance.generate_verify_email_token()
        verify_url = "http://127.0.0.1:8080/success_verify_email.html?token=" + token

        # 发送验证邮件
        # subject = "美多商城邮箱验证"
        # to_email = [instance.email]
        # html_message = '<p>尊敬的用户您好！</p>' \
        #                '<p>感谢您使用美多商城。</p>' \
        #                '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
        #                '<p><a href="%s">%s<a></p>' % (instance.email, verify_url, verify_url)
        # send_mail(subject,"",settings.EMAIL_HOST_USER, to_email, html_message=html_message)

        #异步celery发送验证邮箱验证信息
        print("*"*14)
        send_verify_email.delay([instance.email],verify_url)
        print("--------------")
        return instance
    class Meta:
        model = User
        fields = ("id","email")
        extra_kwargs = {
            'email': {
                'required': True
            }
        }


class UserAddressSerializer(serializers.ModelSerializer):
    """
      用户地址序列化器
      """
    province = serializers.StringRelatedField(read_only=True)
    city = serializers.StringRelatedField(read_only=True)
    district = serializers.StringRelatedField(read_only=True)
    province_id = serializers.IntegerField(label='省ID', required=True)
    city_id = serializers.IntegerField(label='市ID', required=True)
    district_id = serializers.IntegerField(label='区ID', required=True)
    mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$')

    class Meta:
        model = Address
        exclude = ('user', 'is_deleted', 'create_time', 'update_time')
    def create(self, validated_data):
        """保存"""
        #Address模型类中有user属性，将user对象添加到模型类的创建参数中
        validated_data["user"] = self.context['request'].user
        return super().create(validated_data)

class AddressTitleSerializer(serializers.ModelSerializer):
    """
    地址标题
    """
    class Meta:
        model = Address
        fields = ('title',)


class AddUserBrowsingHistorySerializer(serializers.Serializer):
    """
        添加用户浏览历史序列化器
        """
    sku_id = serializers.IntegerField(label="商品SKU编号", min_value=1)

    def validate_sku_id(self, value):
        """
        检验sku_id是否存在
        """
        try:
            SKU.objects.get(id = value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError("该商品不存在")
        return value

    def create(self, validated_data):
        """
           保存
           """
        user_id = self.context['request'].user.id
        sku_id = validated_data['sku_id']
        redis_conn = get_redis_connection("history")
        #删除已存在本商品历史记录
        redis_conn.lrem("history_%s" % user_id, 0, sku_id)
        # 添加新的浏览记录
        redis_conn.lpush("history_%s" % user_id, sku_id)
        # 只保存最多5条记录
        redis_conn.ltrim("history_%s" % user_id, 0, constants.USER_BROWSING_HISTORY_COUNTS_LIMIT - 1)
        return validated_data

class SKUSerializer(serializers.ModelSerializer):
    """
       SKU序列化器
       """
    class Meta:
        model = SKU
        fields = ("id","name",'price', 'default_image_url', 'comments')

