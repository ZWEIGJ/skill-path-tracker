from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.edit import CreateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from .models import LearningGoal

# --- 工具函数：统一计算进度 ---
def get_user_progress(user):
    goals = LearningGoal.objects.filter(user=user)
    total = goals.count()
    completed = goals.filter(is_completed=True).count()
    progress = int((completed / total) * 100) if total > 0 else 0
    return progress, total, completed

# 1. 看板视图
@login_required
def dashboard_view(request):
    goals = LearningGoal.objects.filter(user=request.user)
    progress, total, completed = get_user_progress(request.user)
    
    return render(request, 'goals/dashboard.html', {
        'goals': goals,
        'total_goals': total,
        'completed_goals': completed,
        'progress_percentage': progress,
    })

# 2. 状态切换视图 (AJAX + Regular)
@login_required
def goal_toggle_view(request, pk):
    goal = get_object_or_404(LearningGoal, pk=pk, user=request.user)
    goal.is_completed = not goal.is_completed
    goal.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        progress, total, completed = get_user_progress(request.user)
        return JsonResponse({
            'status': 'success',
            'is_completed': goal.is_completed,
            'progress_percentage': progress,
            'completed_count': completed,
            'total_count': total
        })
    return redirect('dashboard')

# 3. 创建视图 (修正了 fields 缺失和逻辑错误)
class GoalCreateView(LoginRequiredMixin, CreateView):
    model = LearningGoal
    fields = ['title']  # 必须显式声明，解决 ImproperlyConfigured 报错
    template_name = 'goals/goal_form.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        form.instance.user = self.request.user
        # 如果是 AJAX 请求
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            self.object = form.save()
            progress, total, completed = get_user_progress(self.request.user)
            return JsonResponse({
                'status': 'success',
                'goal_id': self.object.pk,
                'goal_title': self.object.title,
                'progress_percentage': progress,
                'completed_count': completed,
                'total_count': total
            })
        return super().form_valid(form)

# 4. 删除视图
class GoalDeleteView(LoginRequiredMixin, DeleteView):
    model = LearningGoal
    success_url = reverse_lazy('dashboard')

    def post(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            self.object = self.get_object()
            self.object.delete()
            progress, total, completed = get_user_progress(request.user)
            return JsonResponse({
                'status': 'success',
                'progress_percentage': progress,
                'completed_count': completed,
                'total_count': total
            })
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)