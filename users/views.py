from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q

from .forms import CustomUserCreationForm, UserProfileForm
from goals.models import LearningGoal, Tag

def register_view(request):
    """处理用户注册"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"欢迎加入，{user.username}！账号已创建并自动登录。")
            return redirect('goal_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile_view(request):
    """
    个人资料页：展示统计数据 + 修改资料
    """
    user = request.user
    
    if request.method == 'POST':
        # 注意：处理图片上传必须传入 request.FILES
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "个人资料已成功更新！")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user)

    # --- 简单的技能路径统计逻辑 ---
    # 获取当前用户已完成的目标总数
    completed_goals_count = LearningGoal.objects.filter(
        user=user, 
        subtasks__is_completed=True
    ).distinct().count()

    # 路径规划雏形：获取前 3 个常用标签及其对应的完成进度
    # 这部分可以作为你以后“升阶”逻辑的基础
    skill_stats = Tag.objects.filter(user=user).annotate(
        num_completed=Count(
            'goals', 
            filter=Q(goals__subtasks__is_completed=True)
        )
    ).order_by('-num_completed')[:3]

    context = {
        'form': form,
        'user': user,
        'completed_goals_count': completed_goals_count,
        'skill_stats': skill_stats,
    }
    
    return render(request, 'users/profile.html', context)