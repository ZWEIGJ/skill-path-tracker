from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from users.views import register_view
# 统一导入 goals 应用的 views 模块
from goals import views 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # --- 目标管理 (Step 4 架构) ---
    
    # 1. 大目标（页面级操作）
    path('', views.goal_list_view, name='goal_list'),             # 首页：大目标卡片流
    path('goal/add/', views.GoalCreateView.as_view(), name='goal_add'),  # 新放大目标（独立页）
    path('goal/<int:pk>/', views.goal_detail_view, name='goal_detail'), # 详情页：拆分任务的舞台
    
    # 2. 子任务（AJAX 纯异步接口）
    path('subtask/add/<int:goal_id>/', views.subtask_add_ajax, name='subtask_add'),
    path('subtask/toggle/<int:pk>/', views.subtask_toggle_ajax, name='subtask_toggle'),
    path('subtask/delete/<int:pk>/', views.subtask_delete_ajax, name='subtask_delete'),
]