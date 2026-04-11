import json
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

from .models import LearningGoal, SubTask
from .forms import LearningGoalForm

# --- 1. 大目标管理 ---

@login_required
def goal_list_view(request):
    """首页：显示大目标列表、统计看板及图表数据"""
    now_date = timezone.now().date()
    
    # 获取当前用户的所有目标（用于全局统计）
    user_goals = LearningGoal.objects.filter(user=request.user)
    
    # 1. 顶部数据统计
    total_count = user_goals.count()
    completed_count = sum(1 for g in user_goals if g.progress >= 100)
    in_progress_count = sum(1 for g in user_goals if 0 < g.progress < 100)
    
    # 本周完成的子任务总数（用于“本周突破”卡片）
    last_7_days = timezone.now() - timedelta(days=7)
    weekly_subtasks = SubTask.objects.filter(
        goal__user=request.user, 
        is_completed=True, 
        updated_at__gte=last_7_days
    ).count()

    # 2. 列表显示：只显示未归档的目标，并进行复杂排序
    goals = user_goals.filter(is_archived=False).annotate(
        total_tasks=Count('subtasks'),
        completed_tasks_count=Count('subtasks', filter=Q(subtasks__is_completed=True)),
        
        # 排序逻辑：未过期 > 高优先级 > 截止日期
        is_overdue_sort=Case(
            When(
                Q(deadline__lt=now_date) & 
                (Q(total_tasks=0) | Q(completed_tasks_count__lt=F('total_tasks'))), 
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

    # 3. 准备 Chart.js 所需的 7 天数据
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
            'completed': completed_count,
            'active': in_progress_count,
            'weekly': weekly_subtasks
        },
        'chart_data_json': json.dumps({'labels': days, 'values': task_counts})
    })

@login_required
def goal_detail_view(request, pk):
    """详情页：展示特定目标的所有子任务"""
    goal = get_object_or_404(LearningGoal, pk=pk, user=request.user)
    subtasks = goal.subtasks.all().order_by('created_at')
    
    return render(request, 'goals/goal_detail.html', {
        'goal': goal,
        'subtasks': subtasks,
        'progress_percentage': goal.progress 
    })

class GoalCreateView(LoginRequiredMixin, CreateView):
    """新建目标页面"""
    model = LearningGoal
    form_class = LearningGoalForm
    template_name = 'goals/goal_form.html'
    success_url = reverse_lazy('goal_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

@login_required
@require_POST
def goal_delete_view(request, pk):
    """删除目标逻辑"""
    goal = get_object_or_404(LearningGoal, pk=pk, user=request.user)
    goal.delete()
    messages.success(request, "目标及其所有关联任务已成功移除。")
    return redirect('goal_list')

@login_required
@require_POST
def goal_archive_ajax(request, pk):
    """归档目标逻辑 (AJAX)"""
    goal = get_object_or_404(LearningGoal, pk=pk, user=request.user)
    goal.is_archived = True
    goal.save()
    return JsonResponse({'status': 'success'})


# --- 2. 子任务管理 (AJAX 接口) ---

@login_required
@require_POST
def subtask_add_ajax(request, goal_id):
    """添加子任务 (AJAX)"""
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
    return JsonResponse({'status': 'error', 'message': '标题不能为空'}, status=400)

@login_required
def subtask_toggle_ajax(request, task_id):
    """切换子任务状态 (AJAX)"""
    subtask = get_object_or_404(SubTask, pk=task_id, goal__user=request.user)
    subtask.is_completed = not subtask.is_completed
    subtask.save()
    
    return JsonResponse({
        'status': 'success',
        'is_completed': subtask.is_completed,
        'progress_percentage': subtask.goal.progress
    })

@login_required
def subtask_delete_ajax(request, task_id):
    """删除子任务 (AJAX)"""
    subtask = get_object_or_404(SubTask, pk=task_id, goal__user=request.user)
    goal = subtask.goal
    subtask.delete()
    
    return JsonResponse({
        'status': 'success',
        'progress_percentage': goal.progress
    })