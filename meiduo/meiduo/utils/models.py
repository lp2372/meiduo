from django.db import models

class BaseModel(models.Model):
    """基础模型补充公共字段"""
    create_time = models.DateTimeField(auto_now_add=True,verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now=True,verbose_name="更新时间")

    class Meta:
        # 声明当前模型只能用于继承，数据迁移不会创建basemodel的表了
        # 抽象类,不能进行实例化的类，而只是被其他子类继承。
        abstract = True