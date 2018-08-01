from django.shortcuts import render
from rest_framework.viewsets import ReadOnlyModelViewSet
from .models import Area
# Create your views here.
from . import serializers
#　
from rest_framework_extensions.cache.mixins import CacheResponseMixin

#在视图中想使用缓存，可以通过为视图添CacheResponseMixin扩展类
class AreasViewSet(CacheResponseMixin,ReadOnlyModelViewSet):
    """
       行政区划信息
       """
    pagination_class = None  # 区划信息不分页

    def get_queryset(self):
        if self.action == "list":
            return Area.objects.filter(parent = None)
        else:
            return Area.objects.all()
    def get_serializer_class(self):
        if self.action == "list":
            return serializers.AreaSerializer
        else:
            return serializers.SubAreaSerializer