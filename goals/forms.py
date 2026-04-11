from django import forms
from .models import LearningGoal

class LearningGoalForm(forms.ModelForm):
    class Meta:
        model = LearningGoal
        fields = ['title', 'description', 'deadline', 'priority']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例如：掌握 Python 数据分析'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '描述一下你达成目标后的样子...'
            }),
            'deadline': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'  # 强制浏览器弹出日期选择器
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'title': '目标名称',
            'description': '详细描述',
            'deadline': '截止日期',
            'priority': '优先级',
        }