from django.conf.urls import url
from users import views
from rest_framework_jwt.views import obtain_jwt_token
from users.utils import UsernameMobileAuthBackend
from rest_framework.routers import DefaultRouter
urlpatterns = [
    url("^usernames/(?P<username>\w{5,20})/count/$",views.UsernameCountView.as_view()),
    url("^mobiles/(?P<mobile>\d{11})/count/$",views.MobileCountView.as_view()),
    url(r"^users/$",views.UserView.as_view()),
    url(r'^authorizations/$', obtain_jwt_token, name='authorizations'),
    url(r'^accounts/(?P<account>\d{11}|\w{5,20})/sms/token/$',views.SMSCodeTokenView.as_view()),
    # url(r"^authorizations/$",UserAuthorizeView,name = 'authorizations'),
    url(r"^sms_codes/$",views.SMSCodeByTokenView.as_view()),
    url(r"^accounts/(?P<account>\w{5,20}|\d{11})/password/token/$",views.PasswordTokenView.as_view()),
    url(r"^users/(?P<pk>\d+)/password/$",views.PasswordView.as_view()),
    url(r"^user/$",views.UserDetailView.as_view()),
    url(r"^emails/$",views.EmailView.as_view()),
    url(r"^emails/verification/$",views.VerifyEmailView.as_view()),
    url(r"^browse_histories/$",views.UserBrowsingHistoryView.as_view()),
]

router = DefaultRouter()
router.register("addresses",views.AddressViewSet,base_name="address")
urlpatterns += router.urls

print(router.urls)