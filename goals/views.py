from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.contrib import messages  # 修复 Pylance 报错的关键导入
from .models import LearningGoal, SubTask

# --- 1. 大目标管理 (页面级) ---

@login_required
def goal_list_view(request):
    """首页：显示所有大目标的卡片"""
    goals = LearningGoal.objects.filter(user=request.user)
    return render(request, 'goals/goal_list.html', {
        'goals': goals,
    })

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
    """创建大目标的独立页面"""
    model = LearningGoal
    fields = ['title', 'description']
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
    # 注意参数名改为了 task_id，与 urls.py 保持一致
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