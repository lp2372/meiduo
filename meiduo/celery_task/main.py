from celery import Celery
import os
#设置环境变量
if not os.getenv("DJANGO_SETTINGS_MODULE"):
    # os.environ["DJANGO_SETTINGS_MODULE"] = "meiduo.settings.dev"
    os.environ.setdefault("DJANGO_SETTINGS_MODULE","meiduo.settings.dev")

#创建celery应用
app = Celery("meiduo")
#加载配置
app.config_from_object("celery_task.config")

app.autodiscover_tasks(["celery_task.sms","celery_task.email","celery_task.html"]) #会自动查找ｔａｓｋｓ模块

#启动celery
#celery -A 主程序的包路径　workon -l info
#一般从后端根目录执行上面命令
#celery -A celery_task.main worker -l info