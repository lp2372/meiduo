from django.shortcuts import render
from rest_framework_extensions.cache.mixins import ListCacheResponseMixin
from rest_framework.generics import ListAPIView
# Create your views here.
from goods.serializers import SKUSerializer
from .models import SKU
class HotSKUListView(ListCacheResponseMixin,ListAPIView):
    """
      热销商品, 使用缓存扩展
      """
    serializer_class = SKUSerializer
    pagination_class = None

    def get_queryset(self):
        category_id = self.kwargs.get("category_id")
        return SKU.objects.filter(category_id =category_id,is_launched = True).order_by("-sales")[0:3]

