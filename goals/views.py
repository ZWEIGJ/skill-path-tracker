import json # 顶部增加导入
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

# --- 1. 大目标管理 (页面级) ---

@login_required
def goal_list_view(request):
    """首页：显示大目标 + 统计数据（逻辑：未过期 > 优先级 > 截止日期）"""
    now_date = timezone.now().date()
    
    # 1. 统计逻辑：计算顶部的四个数字
    all_goals = LearningGoal.objects.filter(user=request.user)
    total_count = all_goals.count()
    # 使用列表推导式计算进度（对应你的模型 @property）
    completed_count = sum(1 for g in all_goals if g.progress >= 100)
    in_progress_count = sum(1 for g in all_goals if 0 < g.progress < 100)
    
    # 本周完成的子任务数
    last_7_days = timezone.now() - timezone.timedelta(days=7)
    weekly_subtasks = SubTask.objects.filter(
        goal__user=request.user, 
        is_completed=True, 
        updated_at__gte=last_7_days
    ).count()

    # 2. 排序逻辑：annotate 必须写在 order_by 之前
    goals = all_goals.annotate(
        total_tasks=Count('subtasks'),
        completed_tasks_count=Count('subtasks', filter=Q(subtasks__is_completed=True)),
        
        # 过期沉底逻辑
        is_overdue_sort=Case(
            When(
                Q(deadline__lt=now_date) & 
                (Q(total_tasks=0) | Q(completed_tasks_count__lt=F('total_tasks'))), 
                then=True
            ),
            default=False,
            output_field=BooleanField()
        ),
        
        # 优先级权重
        priority_weight=Case(
            When(priority='H', then=3),
            When(priority='M', then=2),
            When(priority='L', then=1),
            default=0,
            output_field=IntegerField(),
        )
    ).order_by(
        'is_overdue_sort',    # 未过期的在前
        '-priority_weight',   # 高优先级在前
        'deadline'            # 日期近的在前
    )

# --- Step 6.2：准备图表数据 ---
    days = []
    task_counts = []
    now = timezone.now()

    for i in range(6, -1, -1): # 获取过去 7 天
        date = (now - timedelta(days=i)).date()
        days.append(date.strftime('%m-%d')) # 格式化日期如 "04-11"
        
        # 统计当天完成的子任务数量
        count = SubTask.objects.filter(
            goal__user=request.user,
            is_completed=True,
            updated_at__date=date
        ).count()
        task_counts.append(count)

    # 转换成 JSON 格式供前端 JS 调用
    chart_data = {
        'labels': days,
        'values': task_counts,
    }

    # 修改返回的 context
    return render(request, 'goals/goal_list.html', {
        'goals': goals,
        'stats': {
            'total': total_count,
            'completed': completed_count,
            'active': in_progress_count,
            'weekly': weekly_subtasks
        },
        'chart_data_json': json.dumps(chart_data) # 新增这一行
    })

@login_required
def goal_detail_view(request, pk):
    """详情页：补回了之前失踪的视图函数"""
    goal = get_object_or_404(LearningGoal, pk=pk, user=request.user)
    subtasks = goal.subtasks.all().order_by('created_at')
    
    return render(request, 'goals/goal_detail.html', {
        'goal': goal,
        'subtasks': subtasks,
        'progress_percentage': goal.progress 
    })

class GoalCreateView(LoginRequiredMixin, CreateView):
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
    goal = get_object_or_404(LearningGoal, pk=pk, user=request.user)
    goal.delete()
    messages.success(request, "目标及其所有关联任务已成功移除。")
    return redirect('goal_list')


# --- 2. 子任务管理 (AJAX 接口) ---

@login_required
def subtask_add_ajax(request, goal_id):
    if request.method == 'POST':
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
def subtask_delete_ajax(request, task_id):
    subtask = get_object_or_404(SubTask, pk=task_id, goal__user=request.user)
    goal = subtask.goal
    subtask.delete()
    
    return JsonResponse({
        'status': 'success',
        'progress_percentage': goal.progress
    })