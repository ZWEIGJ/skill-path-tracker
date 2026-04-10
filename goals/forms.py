from django import forms
from .models import LearningGoal

class LearningGoalForm(forms.ModelForm):
    class Meta:
        model = LearningGoal
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': '例如：掌握 Django 核心模型'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': '可选：描述你的学习计划...'}),
        }