from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import LearningGoal

@login_required # 只有登录了才能看
def dashboard_view(request):
    # 获取当前用户的所有目标
    user_goals = LearningGoal.objects.filter(user=request.user)
    return render(request, 'goals/dashboard.html', {'goals': user_goals})