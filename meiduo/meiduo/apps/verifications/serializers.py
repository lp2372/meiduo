from django_redis import get_redis_connection
from rest_framework import serializers

from meiduo.utils.exceptions import logger


class ImageCodeCheckSerializer(serializers.Serializer):
    image_code_id = serializers.UUIDField()
    image_code = serializers.CharField(max_length=4,min_length=4)

    #验证图片验证码
    def validate(self, attrs):
        image_code_id = attrs["image_code_id"]
        image_code = attrs["image_code"]

        redis_conn = get_redis_connection("verify_codes")
        #判断验证码是否存在失效
        real_image_code = redis_conn.get("img_%s" %image_code_id)

        if not real_image_code:
            raise serializers.ValidationError("图片验证码失效")
        #redis中取出数据为bytes类型
        real_image_code = real_image_code.decode()

        #删除图片验证码
        try:
            redis_conn.delete("img_%s" %image_code_id)
        except Exception as e:
            logger.error(e)
        #验证图片验证
        if real_image_code.lower() != image_code.lower():
            raise serializers.ValidationError("验证码错误")

        #验证redis中发送短信标志是否存在
        mobile = self.context['view'].kwargs.get("mobile") # .get() 不存在不报错
        #为了序列化器复用，用于注册以及找回密码第一步
        if mobile:
            send_flg= redis_conn.get("send_flag_%s" %mobile)

            if send_flg:
                raise serializers.ValidationError('请求次数过于频繁')

        return attrs
