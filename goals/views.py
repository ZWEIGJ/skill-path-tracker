import json
import re
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Case, When, IntegerField, Q, BooleanField, F, Count
from django.utils import timezone
from datetime import timedelta

# 导入正确的模型和表单
from .models import LearningGoal, SubTask, Tag 
from .forms import LearningGoalForm

# --- 辅助工具函数 ---

def _process_tags(user, goal, tags_raw):
    """提取字符串中的标签并关联到目标"""
    if tags_raw is None:
        return
    tag_names = re.split(r'[，,\s\n]+', str(tags_raw))
    tag_names = list(set([name.strip() for name in tag_names if name.strip()]))
    
    goal.tags.clear()
    for name in tag_names:
        tag_obj, created = Tag.objects.get_or_create(
            name=name,
            user=user
        )
        goal.tags.add(tag_obj)

# --- 1. 大目标管理 ---

@login_required
def goal_list_view(request):
    """首页：显示大目标列表及统计数据"""
    now_date = timezone.now().date()
    user_goals = LearningGoal.objects.filter(user=request.user)
    
    total_count = user_goals.count()
    completed_real_count = user_goals.filter(is_completed=True).count()
    active_display_count = user_goals.filter(is_archived=False).count()
    archived_count = user_goals.filter(is_archived=True).count()
    
    # 首页周动态：展示最近7天完成的子任务数量
    last_7_days = timezone.now() - timedelta(days=7)
    weekly_subtasks = SubTask.objects.filter(
        goal__user=request.user, 
        is_completed=True, 
        updated_at__gte=last_7_days # 使用 updated_at 更准确反映完成时间
    ).count()

    goals = user_goals.filter(is_archived=False).prefetch_related('tags').annotate(
        total_tasks=Count('subtasks'),
        completed_tasks_count=Count('subtasks', filter=Q(subtasks__is_completed=True)),
        is_overdue_sort=Case(
            When(
                Q(deadline__lt=now_date) & Q(is_completed=False), 
                then=True
            ),
            default=False,
            output_field=BooleanField()
        ),
        priority_weight=Case(
            When(priority='H', then=3),
            When(priority='M', then=2),
            When(priority='L', then=1),
            default=0,
            output_field=IntegerField(),
        )
    ).order_by('is_overdue_sort', '-priority_weight', 'deadline')

    # 图表数据：最近7天每日完成情况
    days = []
    task_counts = []
    now = timezone.now()
    for i in range(6, -1, -1):
        date = (now - timedelta(days=i)).date()
        days.append(date.strftime('%m-%d'))
        count = SubTask.objects.filter(
            goal__user=request.user,
            is_completed=True,
            updated_at__date=date
        ).count()
        task_counts.append(count)

    return render(request, 'goals/goal_list.html', {
        'goals': goals,
        'stats': {
            'total': total_count,
            'completed': completed_real_count,
            'active': active_display_count,
            'archived_count': archived_count,
            'weekly': weekly_subtasks
        },
        'chart_data_json': json.dumps({'labels': days, 'values': task_counts})
    })

@login_required
def goal_detail_view(request, pk):
    """详情页：展示目标及其子任务"""
    goal = get_object_or_404(
        LearningGoal.objects.prefetch_related('tags'), 
        pk=pk, 
        user=request.user
    )
    subtasks = goal.subtasks.all().order_by('is_completed', 'created_at')
    initial_tags_str = ", ".join(tag.name for tag in goal.tags.all())
    
    return render(request, 'goals/goal_detail.html', {
        'goal': goal,
        'subtasks': subtasks,
        'initial_tags': initial_tags_str,
        'progress_percentage': goal.progress 
    })

@login_required
@require_POST
def goal_update_ajax(request, pk):
    """AJAX：更新目标的基础字段"""
    goal = get_object_or_404(LearningGoal, pk=pk, user=request.user)
    field = request.POST.get('field')
    value = request.POST.get('value', '').strip()

    if field == 'title':
        goal.title = value
    elif field == 'description':
        goal.description = value
    elif field == 'deadline':
        goal.deadline = value if value else None
    elif field == 'tags':
        _process_tags(request.user, goal, value)
        tags_html = "".join([f'<span class="custom-tag-detail"># {tag.name}</span>' for tag in goal.tags.all()])
        goal.save()
        return JsonResponse({'status': 'success', 'tags_html': tags_html})
    
    goal.save()
    return JsonResponse({'status': 'success'})

class GoalCreateView(LoginRequiredMixin, CreateView):
    """新建目标页面"""
    model = LearningGoal
    form_class = LearningGoalForm
    template_name = 'goals/goal_form.html'
    success_url = reverse_lazy('goal_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        tags_raw = self.request.POST.get('tags_data') or self.request.POST.get('tags') or ""
        _process_tags(self.request.user, self.object, tags_raw)
        return response

# --- 2. AJAX 接口 (任务与归档) ---

@login_required
@require_POST
def goal_delete_view(request, pk):
    """彻底删除目标"""
    goal = get_object_or_404(LearningGoal, pk=pk, user=request.user)
    goal.delete()
    messages.success(request, "目标已删除。")
    return redirect('goal_list')

@login_required
@require_POST
def goal_archive_ajax(request, pk):
    """
    AJAX：归档目标
    修复：在归档时记录当前时间
    """
    goal = get_object_or_404(LearningGoal, pk=pk, user=request.user)
    goal.is_archived = True
    goal.archived_at = timezone.now() # 🌟 记录归档时刻
    goal.save()
    return JsonResponse({'status': 'success'})

@login_required
@require_POST
def subtask_add_ajax(request, goal_id):
    goal = get_object_or_404(LearningGoal, pk=goal_id, user=request.user)
    title = request.POST.get('title', '').strip()
    if title:
        subtask = SubTask.objects.create(goal=goal, title=title)
        return JsonResponse({
            'status': 'success',
            'task_id': subtask.id,
            'task_title': subtask.title,
            'progress_percentage': goal.progress
        })
    return JsonResponse({'status': 'error'}, status=400)

@login_required
@require_POST
def subtask_toggle_ajax(request, task_id):
    subtask = get_object_or_404(SubTask, pk=task_id, goal__user=request.user)
    subtask.is_completed = not subtask.is_completed
    subtask.save()
    return JsonResponse({
        'status': 'success',
        'is_completed': subtask.is_completed,
        'progress_percentage': subtask.goal.progress
    })

@login_required
@require_POST
def subtask_delete_ajax(request, task_id):
    subtask = get_object_or_404(SubTask, pk=task_id, goal__user=request.user)
    goal = subtask.goal
    subtask.delete()
    return JsonResponse({
        'status': 'success',
        'progress_percentage': goal.progress
    })

# --- 3. 归档实验室 ---

@login_required
def archived_goals_view(request):
    """
    已归档列表：展示成就墙与本周突破
    """
    # 🌟 优化：按归档时间排序，最近归档的排最前
    archived_goals = LearningGoal.objects.filter(
        user=request.user, 
        is_archived=True
    ).prefetch_related('tags').order_by('-archived_at')

    # 图表统计：统计归档目标中不同标签的分布
    tag_counts = Tag.objects.filter(
        goals__user=request.user,
        goals__is_archived=True
    ).annotate(num_goals=Count('goals', filter=Q(goals__is_archived=True))).order_by('-num_goals')

    chart_labels = [tag.name for tag in tag_counts] or ["暂无数据"]
    chart_values = [tag.num_goals for tag in tag_counts] or [0]

    # 🌟 修复“本周突破”逻辑 Bug：
    # 计算本周（周一凌晨起）内归档的目标数量，而非创建时间
    now = timezone.now()
    start_of_week = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    
    weekly_archived_count = archived_goals.filter(archived_at__gte=start_of_week).count()

    return render(request, 'goals/archived_list.html', {
        'goals': archived_goals,
        'weekly_count': weekly_archived_count,
        'total_achievements': archived_goals.count(),
        'chart_labels_json': json.dumps(chart_labels),
        'chart_values_json': json.dumps(chart_values),
    })

@login_required
@require_POST
def goal_restore_ajax(request, pk):
    """从归档中恢复目标"""
    goal = get_object_or_404(LearningGoal, pk=pk, user=request.user)
    goal.is_archived = False
    goal.archived_at = None # 恢复时清除归档时间戳
    goal.save()
    return JsonResponse({'status': 'success'})