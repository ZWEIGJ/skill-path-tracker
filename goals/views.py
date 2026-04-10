from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.edit import CreateView
from django.views.generic.edit import DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import LearningGoal
from .forms import LearningGoalForm
from django.http import JsonResponse

# 1. 看板视图：显示当前登录用户的目标
@login_required
def dashboard_view(request):
    goals = LearningGoal.objects.filter(user=request.user)
    
    # TDD 核心逻辑：计算进度
    total = goals.count()
    completed = goals.filter(is_completed=True).count()
    
    # 严谨的百分比计算
    progress_percentage = int((completed / total) * 100) if total > 0 else 0
    
    return render(request, 'goals/dashboard.html', {
        'goals': goals,
        'total_goals': total,
        'completed_goals': completed,
        'progress_percentage': progress_percentage,
    })

def goal_toggle_view(request, pk):
    goal = get_object_or_404(LearningGoal, pk=pk, user=request.user)
    goal.is_completed = not goal.is_completed
    goal.save()

    # 如果是 AJAX 请求，返回 JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # 重新计算进度（逻辑复用）
        goals = LearningGoal.objects.filter(user=request.user)
        total = goals.count()
        completed = goals.filter(is_completed=True).count()
        progress = int((completed / total) * 100) if total > 0 else 0
        
        return JsonResponse({
            'status': 'success',
            'is_completed': goal.is_completed,
            'progress_percentage': progress,
            'completed_count': completed,
            'total_count': total
        })

    # 否则（普通点击），依然跳转回看板
    return redirect('dashboard')

# 2. 创建视图：处理添加逻辑
class GoalCreateView(LoginRequiredMixin, CreateView):
    model = LearningGoal
    form_class = LearningGoalForm
    template_name = 'goals/goal_form.html'
    success_url = reverse_lazy('dashboard') # 保存成功后跳回看板

    def form_valid(self, form):
        # 核心：将当前登录的用户自动赋值给目标的 user 字段
        form.instance.user = self.request.user
        return super().form_valid(form)
    
class GoalDeleteView(LoginRequiredMixin, DeleteView):
    model = LearningGoal
    success_url = reverse_lazy('dashboard')

    def get_queryset(self):
        """这一步是核心：确保查询集只包含当前登录用户自己的目标"""
        return self.model.objects.filter(user=self.request.user)