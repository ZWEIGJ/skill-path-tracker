from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # 在用户列表中显示的列，让你一眼看到所有人的技能水平
    list_display = ('username', 'email', 'skill_level', 'is_staff')
    
    # 在修改用户详情页时，增加一个“技能画像”区块
    fieldsets = UserAdmin.fieldsets + (
        ("技能画像", {'fields': ('skill_level', 'skill_tags')}),
    )