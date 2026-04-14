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
    个人资料页：展示按标签独立进化的技能路径 + 修改资料
    """
    user = request.user
    
    # 1. 处理资料更新表单 (包含头像上传)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "个人资料已成功更新！")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user)

    # 2. 定义进化等级标准 (阈值, 名称, 颜色)
    # 提示：如果当前目标数较少，可以把 20, 15 等数字调小以便测试
    RANK_STAGES = [
        (20, "钻石", "#4dc3ff"),
        (15, "白金", "#6c757d"),
        (10, "黄金", "#ffd700"),
        (5,  "白银", "#c0c0c0"),
        (0,  "青铜", "#cd7f32"),
    ]

    # 3. 核心统计逻辑：按标签独立计数
    # 关键点：Count('goals') 是因为 LearningGoal 模型里 tags 字段定义了 related_name='goals'
    tag_stats_query = Tag.objects.filter(user=user).annotate(
        goal_count=Count('goals') 
    ).order_by('-goal_count')

    skill_stats = []
    for tag in tag_stats_query:
        count = tag.goal_count
        
        # 匹配当前标签符合的最高 Rank 阶段
        tag_rank = "青铜"
        tag_color = "#cd7f32"
        for threshold, name, color in RANK_STAGES:
            if count >= threshold:
                tag_rank = name
                tag_color = color
                break 
        
        # 计算进度条百分比 (以 20 个目标作为 100% 满进度)
        progress_percent = min((count / 20) * 100, 100)
        
        skill_stats.append({
            'name': tag.name,
            'total_count': count,
            'rank': tag_rank,
            'rank_color': tag_color,
            'percent': progress_percent
        })

    # 4. 获取总完成目标数
    # 只要是归档状态 (is_archived=True) 的目标都算作已完成
    completed_total = LearningGoal.objects.filter(user=user, is_archived=True).count()

    context = {
        'form': form,
        'user': user,
        'completed_goals_count': completed_total,
        'skill_stats': skill_stats,
    }
    
    return render(request, 'users/profile.html', context)