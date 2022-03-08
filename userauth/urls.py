from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('nicknamechange/', views.nicknamechange, name='nicknamechange'),
    path('pwchange/', views.pwchange, name='pwchange'),
    path('inactive/', views.inactive, name='inactive'),
 ]