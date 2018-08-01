from rest_framework import serializers
from .models import Area
class AreaSerializer(serializers.ModelSerializer):
    """
        行政区划信息序列化器
        """
    class Meta:
        model = Area
        fields = ("id","name")

class SubAreaSerializer(serializers.ModelSerializer):
    """
       子行政区划信息序列化器
       """
    # read_only 表示反序列化是不能使用，序列化关联对象多个时候需设置many=TRUE
    subs = AreaSerializer(many=True,read_only=True)
    class Meta:
        model = Area
        fields = ("id","name","subs")