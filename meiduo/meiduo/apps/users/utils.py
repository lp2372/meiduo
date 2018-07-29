import re
from django.contrib.auth.backends import ModelBackend
# Django REST framework JWT提供了登录获取token的视图，可以直接使用
# 但是默认的返回值仅有token，我们还需在返回值中增加username和user_id。
# 通过修改该视图的返回值可以完成我们的需求。
def jwt_response_payload_handler(token, user=None, request=None):
    """
     自定义jwt认证成功返回的数据
    :param token: 登陆视图中的jwt
    :param user:  当前登陆的用户对象
    :param request: 当前登陆请求信息
    :return: dic

    """
    return {
        "token":token,
        "user_id":user.id,
        "username":user.username
    }

# JWT扩展的登录视图，在收到用户名与密码时，也是调用Django的认证系统中提供的authenticate()来检查用户名与密码是否正确。
#
# 我们可以通过修改Django认证系统的认证后端（主要是authenticate方法）来支持登录账号既可以是用户名也可以是手机号。
from users.models import User
def get_user_by_account(account):
    """
       根据帐号获取user对象
       :param account: 账号，可以是用户名，也可以是手机号
       :return: User对象 或者 None
       """
    try:
        if re.match(r"^\d{11}$",account):
            # 帐号为手机号
            user = User.objects.get(mobile=account)
        else:
            # 帐号为用户名
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        return None
    else:
        return user

class UsernameMobileAuthBackend(ModelBackend):
    """
       自定义用户名或手机号认证
       """
    # 修改Django认证系统的认证后端需要继承ModelBackend，并重写authenticate方法。
    def authenticate(self, request, username=None, password=None, **kwargs):
        # 根据username参数查找用户User对象，username参数可能是用户名，也可能是手机号
        # 若查找到User对象，调用User对象的check_password方法检查密码是否正确
        print("-------------------------")
        user = get_user_by_account(username)
        if user is not None and user.check_password(password):
            return user
