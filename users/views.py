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
    个人资料页：展示按标签独立进化的技能路径
    修复：使用 goals__is_completed (双下划线) 解决跨表字段查询报错
    """
    user = request.user
    
    # 1. 处理资料更新表单
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "个人资料已成功更新！")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user)

    # 2. 等级标准
    RANK_STAGES = [
        (20, "钻石", "#4dc3ff"),
        (15, "白金", "#6c757d"),
        (10, "黄金", "#ffd700"),
        (5,  "白银", "#c0c0c0"),
        (0,  "青铜", "#cd7f32"),
    ]

    # 3. 核心统计逻辑
    # 注意：filter 中的 Q 对象必须使用 goals__前缀，因为是从 Tag 查 Goal [cite: 41, 149]
    tag_stats_query = Tag.objects.filter(user=user).annotate(
        # 修复关键：确保查询路径通过双下划线正确指向 LearningGoal 的布尔字段
        achieved_count=Count(
            'goals', 
            filter=Q(goals__is_completed=True) & Q(goals__is_archived=True)
        ),
        total_related_count=Count('goals')
    ).order_by('-achieved_count')

    skill_stats = []
    for tag in tag_stats_query:
        # 排除已删除目标后留下的“孤儿标签”
        if tag.total_related_count == 0:
            continue
            
        count = tag.achieved_count
        
        tag_rank = "青铜"
        tag_color = "#cd7f32"
        for threshold, name, color in RANK_STAGES:
            if count >= threshold:
                tag_rank = name
                tag_color = color
                break 
        
        progress_percent = min((count / 20) * 100, 100)
        
        skill_stats.append({
            'name': tag.name,
            'total_count': count,
            'rank': tag_rank,
            'rank_color': tag_color,
            'percent': progress_percent
        })

    # 4. 总完成数统计
    # 直接查询 LearningGoal 模型，字段名不带前缀 
    completed_total = LearningGoal.objects.filter(
        user=user, 
        is_completed=True, 
        is_archived=True
    ).count()

    context = {
        'form': form,
        'user': user,
        'completed_goals_count': completed_total,
        'skill_stats': skill_stats,
    }
    
    return render(request, 'users/profile.html', context)