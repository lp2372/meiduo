from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from fdfs_client.client import Fdfs_client
from django.conf import settings

@deconstructible
class FastDFSStorage(Storage):
    """自定义FastDFS存储文件的存储"""
    def __init__(self,base_url = None,client_conf = None):
        """
       初始化
       :param base_url: 用于构造图片完整路径使用，图片服务器的域名
       :param client_conf: FastDFS客户端配置文件的路径
       """

        # 支持Django不带任何参数来实例化存储类，也就是说任何设置都应该从django.conf.settings中获取
        if base_url is None:
            base_url = settings.FDFS_URL
        self.base_url = base_url
        if client_conf is None:
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf

    def _open(self,name,model='rb'):

        # 存储类中必须实现_open()和_save()方法，以及任何后续使用中可能用到的其他方法。

        pass
    def _save(self,name,content):
        """
       在FastDFS中保存文件
       :param name: 传入的文件名
       :param content: 文件内容
       :return: 保存到数据库中的FastDFS的文件名
       """
        client = Fdfs_client(self.client_conf)
        ret = client.upload_appender_by_buffer(content.read())
        if ret.get("Status") != 'Upload successed.':
            raise Exception("upload file failed")
        file_name = ret.get("Remote file_id")

        return file_name

    def url(self, name):
        """
        返回文件的完整URL路径
        :param name:  数据库中间保存文件名
        :return: 　完整url　路径
        """
        return self.base_url + name
    def exists(self, name):
        """
           判断文件是否存在，FastDFS可以自行解决文件的重名问题
           所以此处返回False，告诉Django上传的都是新文件
           :param name:  文件名
           :return: False
               """
        return False
