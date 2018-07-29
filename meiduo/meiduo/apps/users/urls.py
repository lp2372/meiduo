from django.conf.urls import url
from users import views
from rest_framework_jwt.views import obtain_jwt_token
from users.utils import UsernameMobileAuthBackend
urlpatterns = [
    url("^usernames/(?P<username>\w{5,20})/count/$",views.UsernameCountView.as_view()),
    url("^mobiles/(?P<mobile>\d{11})/count/$",views.MobileCountView.as_view()),
    url(r"^users/$",views.UserView.as_view()),
    url(r'authorizations/', obtain_jwt_token, name='authorizations'),
    # url(r"^authorizations/$",UserAuthorizeView,name = 'authorizations'),
]