from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from users.views import register_view
from goals import views 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # --- 1. 大目标（页面级操作） ---
    path('', views.goal_list_view, name='goal_list'),
    path('goal/add/', views.GoalCreateView.as_view(), name='goal_add'),
    path('goal/<int:pk>/', views.goal_detail_view, name='goal_detail'),
    path('goal/<int:pk>/delete/', views.goal_delete_view, name='goal_delete'), # 建议路径加个前缀更清晰
    
    # --- 2. 子任务（AJAX 纯异步接口） ---
    # 这里的变量名 goal_id 和 task_id 必须和 views.py 的函数参数名完全一致
    path('subtask/add/<int:goal_id>/', views.subtask_add_ajax, name='subtask_add'),
    path('subtask/toggle/<int:task_id>/', views.subtask_toggle_ajax, name='subtask_toggle'),
    path('subtask/delete/<int:task_id>/', views.subtask_delete_ajax, name='subtask_delete'),
]