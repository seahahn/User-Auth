from django.urls import path, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from . import views

schema_view = get_schema_view(
   openapi.Info(
      title="AI Play User-Auth API",
      default_version='v1',
      description="""
      For user authentication and authorization API

      ### Tags
      - #### check : 이메일, 닉네임 체크를 위한 API
      - #### auth : 로그인, 회원가입, 사용자 탈퇴를 위한 API
      - #### token : CSRF 토큰 및 JWT 발급, 갱신, 삭제를 위한 API
      - #### change : 사용자 정보 변경을 위한 API
      """,
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)

urlpatterns = [
   re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
   re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
   re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

   path('index', views.index, name='index'),
   path('nickname_check', views.nickname_check, name='nickname_check'),
   path('email_check', views.email_check, name='email_check'),
   path('email_confirm', views.email_confirm, name='email_confirm'),
   path('signup', views.signup, name='signup'),
   path('login', views.login, name='login'),
   path('search_pw', views.search_pw, name='search_pw'),
   path('nickname_change', views.nicknamechange, name='nickname_change'),
   path('pw_change', views.pwchange, name='pwchange'),
   path('profile_pic_change', views.profile_pic_change, name='profile_pic_change'),
   path('inactive', views.inactive, name='inactive'),

   path('refresh_jwt', views.refresh_jwt, name='refresh_jwt'),
   path('remove_jwt', views.remove_jwt, name='remove_jwt')
]