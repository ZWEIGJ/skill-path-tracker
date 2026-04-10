from django.shortcuts import render, redirect
from django.contrib.auth import login  # 导入登录函数
from .forms import CustomUserCreationForm
from django.contrib import messages # 导入消息通知

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"欢迎加入，{user.username}！账号已创建并自动登录。")
            return redirect('goal_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})