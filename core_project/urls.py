"""
URL configuration for core_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from users.views import register_view  # 导入刚才写的视图
from django.contrib.auth import views as auth_views # 引入内置认证视图
from goals.views import (
    dashboard_view, 
    goal_toggle_view, 
    GoalCreateView, 
    GoalDeleteView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Goals 模块
    path('', dashboard_view, name='dashboard'),
    path('add/', GoalCreateView.as_view(), name='goal_add'),
    path('delete/<int:pk>/', GoalDeleteView.as_view(), name='goal_delete'),
    
    # 这里是之前的报错重灾区：确保函数名是 goal_toggle_view
    path('toggle/<int:pk>/', goal_toggle_view, name='goal_toggle'),
]