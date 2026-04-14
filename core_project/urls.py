from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

# 导入视图
from users.views import register_view, profile_view
from goals import views as goal_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- 1. 用户系统 ---
    path('register/', register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', profile_view, name='profile'), # 刚才新写的个人中心

    # --- 2. 大目标管理 (页面操作) ---
    path('', goal_views.goal_list_view, name='goal_list'),
    path('goal/add/', goal_views.GoalCreateView.as_view(), name='goal_add'),
    path('goal/<int:pk>/', goal_views.goal_detail_view, name='goal_detail'),
    path('goal/<int:pk>/delete/', goal_views.goal_delete_view, name='goal_delete'),
    
    # 归档功能
    path('archived/', goal_views.archived_goals_view, name='archived_goals'),
    path('goal/archive/<int:pk>/', goal_views.goal_archive_ajax, name='goal_archive_ajax'),
    path('goal/restore/<int:pk>/', goal_views.goal_restore_ajax, name='goal_restore_ajax'),
    
    # --- 3. 子任务 (AJAX 接口) ---
    path('subtask/add/<int:goal_id>/', goal_views.subtask_add_ajax, name='subtask_add'),
    path('subtask/toggle/<int:task_id>/', goal_views.subtask_toggle_ajax, name='subtask_toggle'),
    path('subtask/delete/<int:task_id>/', goal_views.subtask_delete_ajax, name='subtask_delete'),
]

# --- 4. 媒体文件与静态文件访问 (开发环境必需) ---
# 如果没有这两行，你上传的头像在网页上会显示为红叉或 404
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)