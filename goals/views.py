from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import LearningGoal
from .forms import LearningGoalForm

# 1. 看板视图：显示当前登录用户的目标
@login_required
def dashboard_view(request):
    user_goals = LearningGoal.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'goals/dashboard.html', {'goals': user_goals})
def toggle_goal_view(request, pk):
    # 关键：查询时带上 user=request.user，确保越权隔离
    goal = get_object_or_404(LearningGoal, pk=pk, user=request.user)
    goal.is_completed = not goal.is_completed
    goal.save()
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