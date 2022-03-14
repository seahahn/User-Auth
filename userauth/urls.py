from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('nickname_check/', views.nickname_check, name='nickname_check'),
    path('email_check/', views.email_check, name='email_check'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('search_pw/', views.search_pw, name='search_pw'),
    path('nickname_change/', views.nicknamechange, name='nickname_change'),
    path('pw_change/', views.pwchange, name='pwchange'),
    path('profile_pic_change/', views.profile_pic_change, name='profile_pic_change'),
    path('inactive/', views.inactive, name='inactive'),
 ]