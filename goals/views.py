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

# 确保导入了正确的模型和表单
from .models import LearningGoal, SubTask, Tag 
from .forms import LearningGoalForm

# --- 1. 大目标管理 ---

@login_required
def goal_list_view(request):
    """首页：显示大目标列表、统计看板及图表数据"""
    now_date = timezone.now().date()
    
    user_goals = LearningGoal.objects.filter(user=request.user)
    
    total_count = user_goals.count()
    completed_real_count = sum(1 for g in user_goals if g.progress >= 100)
    active_display_count = user_goals.filter(is_archived=False).count()
    archived_count = user_goals.filter(is_archived=True).count()
    
    last_7_days = timezone.now() - timedelta(days=7)
    weekly_subtasks = SubTask.objects.filter(
        goal__user=request.user, 
        is_completed=True, 
        created_at__gte=last_7_days 
    ).count()

    # 列表显示：prefetch_related 确保标签能被一次性查出
    goals = user_goals.filter(is_archived=False).prefetch_related('tags').annotate(
        total_tasks=Count('subtasks'),
        completed_tasks_count=Count('subtasks', filter=Q(subtasks__is_completed=True)),
        
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

    # 准备主页趋势图数据
    days = []
    task_counts = []
    now = timezone.now()
    for i in range(6, -1, -1):
        date = (now - timedelta(days=i)).date()
        days.append(date.strftime('%m-%d'))
        count = SubTask.objects.filter(
            goal__user=request.user,
            is_completed=True,
            created_at__date=date
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
    """详情页：展示特定目标的所有子任务"""
    goal = get_object_or_404(
        LearningGoal.objects.prefetch_related('tags'), 
        pk=pk, 
        user=request.user
    )
    subtasks = goal.subtasks.all().order_by('is_completed', 'created_at')
    
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
        response = super().form_valid(form)
        
        tags_raw = self.request.POST.get('tags_data') or self.request.POST.get('tags') or ""
        if tags_raw:
            tag_names = re.split(r'[，,\s\n]+', tags_raw)
            tag_names = list(set([name.strip() for name in tag_names if name.strip()]))
            for name in tag_names:
                tag_obj, created = Tag.objects.get_or_create(
                    name=name,
                    user=self.request.user
                )
                self.object.tags.add(tag_obj)
        return response

# --- 2. AJAX 接口 (任务与归档) ---

@login_required
@require_POST
def goal_delete_view(request, pk):
    goal = get_object_or_404(LearningGoal, pk=pk, user=request.user)
    goal.delete()
    messages.success(request, "目标已删除。")
    return redirect('goal_list')

@login_required
@require_POST
def goal_archive_ajax(request, pk):
    goal = get_object_or_404(LearningGoal, pk=pk, user=request.user)
    goal.is_archived = True
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

# --- 3. 归档实验室 (增强版) ---

# --- 3. 归档实验室 (修复版) ---

@login_required
def archived_goals_view(request):
    """显示已归档目标，包含环形图分布统计"""
    # 1. 基础查询
    archived_goals = LearningGoal.objects.filter(
        user=request.user, 
        is_archived=True
    ).prefetch_related('tags').order_by('-created_at')

    # 2. 环形图数据：将 learninggoal 替换为 goals (根据报错提示的 choices)
    tag_counts = Tag.objects.filter(
        goals__user=request.user,     # 这里改为 goals__user
        goals__is_archived=True       # 这里改为 goals__is_archived
    ).annotate(num_goals=Count('goals')).order_by('-num_goals') # 这里改为 Count('goals')

    chart_labels = [tag.name for tag in tag_counts]
    chart_values = [tag.num_goals for tag in tag_counts]

    # 如果没有任何带标签的归档，给个默认提示数据
    if not chart_labels:
        chart_labels = ["暂无数据"]
        chart_values = [0]

    # 3. 本周完成统计
    last_7_days = timezone.now() - timedelta(days=7)
    weekly_archived_count = archived_goals.filter(created_at__gte=last_7_days).count()

    return render(request, 'goals/archived_list.html', {
        'goals': archived_goals,
        'weekly_count': weekly_archived_count,
        'chart_labels_json': json.dumps(chart_labels),
        'chart_values_json': json.dumps(chart_values),
    })

@login_required
@require_POST
def goal_restore_ajax(request, pk):
    goal = get_object_or_404(LearningGoal, pk=pk, user=request.user)
    goal.is_archived = False
    goal.save()
    return JsonResponse({'status': 'success'})