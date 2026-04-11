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

from .models import LearningGoal, SubTask
from .forms import LearningGoalForm

# --- 1. 大目标管理 (页面级) ---

@login_required
def goal_list_view(request):
    """首页：显示大目标（逻辑：未过期 > 优先级 > 截止日期）"""
    now_date = timezone.now().date()
    
    # 使用 annotate 预先计算子任务统计信息，用于沉底判断
    goals = LearningGoal.objects.filter(user=request.user).annotate(
        total_tasks=Count('subtasks'),
        completed_tasks=Count('subtasks', filter=Q(subtasks__is_completed=True)),
        
        # 核心沉底逻辑：
        # 判定条件：日期早于今天 AND (没有任务 OR 已完成任务数 < 总任务数)
        is_overdue_sort=Case(
            When(
                Q(deadline__lt=now_date) & 
                (Q(total_tasks=0) | Q(completed_tasks__lt=F('total_tasks'))), 
                then=True
            ),
            default=False,
            output_field=BooleanField()
        ),
        
        # 优先级权重分：高(3) > 中(2) > 低(1)
        priority_weight=Case(
            When(priority='H', then=3),
            When(priority='M', then=2),
            When(priority='L', then=1),
            default=0,
            output_field=IntegerField(),
        )
    ).order_by(
        'is_overdue_sort',    # 1. 未过期的在前 (False/0 < True/1)
        '-priority_weight',   # 2. 权重分高的在前
        'deadline'            # 3. 日期近的在前
    )

    return render(request, 'goals/goal_list.html', {'goals': goals})

@login_required
def goal_detail_view(request, pk):
    """详情页：大目标的详情 + 子任务列表"""
    goal = get_object_or_404(LearningGoal, pk=pk, user=request.user)
    subtasks = goal.subtasks.all().order_by('created_at')
    
    return render(request, 'goals/goal_detail.html', {
        'goal': goal,
        'subtasks': subtasks,
        'progress_percentage': goal.progress 
    })

class GoalCreateView(LoginRequiredMixin, CreateView):
    """创建目标视图"""
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
    """删除大目标及其关联的所有子任务"""
    goal = get_object_or_404(LearningGoal, pk=pk, user=request.user)
    goal.delete()
    messages.success(request, "目标及其所有关联任务已成功移除。")
    return redirect('goal_list')


# --- 2. 子任务管理 (AJAX 纯异步接口) ---

@login_required
def subtask_add_ajax(request, goal_id):
    """异步添加子任务"""
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
    """异步切换子任务状态"""
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
    """异步删除子任务"""
    subtask = get_object_or_404(SubTask, pk=task_id, goal__user=request.user)
    goal = subtask.goal
    subtask.delete()
    
    return JsonResponse({
        'status': 'success',
        'progress_percentage': goal.progress
    })