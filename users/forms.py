from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    """
    用户注册表单：在原有注册字段基础上增加技能水平和初始技能标签
    """
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        # 这里的 fields 包含了系统默认的 username 以及我们自定义的技能字段
        fields = UserCreationForm.Meta.fields + ('skill_level', 'skill_tags')


class UserProfileForm(forms.ModelForm):
    """
    用户资料编辑表单：用于 Profile 页面让用户自由修改信息
    """
    class Meta:
        model = CustomUser
        # 允许用户在 Profile 页面修改的字段
        fields = ['nickname', 'avatar', 'skill_level', 'skill_tags', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': '介绍一下你自己吧...'}),
            'skill_tags': forms.TextInput(attrs={'placeholder': '例如: Python, Django, 机器学习'}),
            'nickname': forms.TextInput(attrs={'placeholder': '想让大家怎么称呼你？'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 给所有字段统一添加 Bootstrap 或自定义的 CSS 类名（可选）
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})