from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('register')
        else:
            # 这一行是关键：如果验证失败，在终端打印出具体原因
            print(f"表单验证失败原因: {form.errors}")
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})