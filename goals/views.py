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

    # 准备图表数据
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
    """详情页：展示特定目标的所有子任务，并预加载标签"""
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
    """新建目标页面：手动处理多对多关联以避免 AttributeErrors"""
    model = LearningGoal
    form_class = LearningGoalForm
    template_name = 'goals/goal_form.html'
    success_url = reverse_lazy('goal_list')

    def form_valid(self, form):
        # 1. 绑定当前用户
        form.instance.user = self.request.user
        
        # 2. 先调用父类的保存逻辑，这会创建 self.object (目标实例)
        # 注意：这里我们不再依赖 form.save_m2m()
        response = super().form_valid(form)
        
        # 3. 获取并解析标签数据
        # 优先拿隐藏域 tags_data，其次拿普通输入框 tags
        tags_raw = self.request.POST.get('tags_data') or self.request.POST.get('tags') or ""
        
        if tags_raw:
            # 使用正则支持：中文逗号、英文逗号、空格、回车作为分隔符
            tag_names = re.split(r'[，,\s\n]+', tags_raw)
            # 去重且过滤空字符串
            tag_names = list(set([name.strip() for name in tag_names if name.strip()]))
            
            for name in tag_names:
                # get_or_create 确保标签唯一，models 中已设置默认颜色
                tag_obj, created = Tag.objects.get_or_create(
                    name=name,
                    user=self.request.user
                )
                # 直接手动添加到多对多关联中
                self.object.tags.add(tag_obj)
        
        return response

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
@require_POST
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
@require_POST
def subtask_delete_ajax(request, task_id):
    """删除子任务 (AJAX)"""
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
    """显示所有已归档的目标，预加载标签以解决“未分类”问题"""
    archived_goals = LearningGoal.objects.filter(
        user=request.user, 
        is_archived=True
    ).prefetch_related('tags').order_by('-created_at') 
    
    return render(request, 'goals/archived_list.html', {
        'goals': archived_goals
    })

@login_required
@require_POST
def goal_restore_ajax(request, pk):
    """将目标从归档状态恢复到激活状态"""
    goal = get_object_or_404(LearningGoal, pk=pk, user=request.user)
    goal.is_archived = False
    goal.save()
    return JsonResponse({'status': 'success'})