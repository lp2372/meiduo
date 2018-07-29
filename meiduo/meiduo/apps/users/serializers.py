import re

from django_redis import get_redis_connection
from rest_framework import serializers
from users.models import User
from rest_framework_jwt.settings import api_settings #引入jwt

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
