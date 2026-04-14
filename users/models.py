from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    """
    自定义用户模型：整合技能水平、标签、头像及简介。
    """
    # 1. 技能等级定义
    SKILL_LEVEL_CHOICES = [
        ('beginner', '初学者'),
        ('intermediate', '进阶者'),
        ('expert', '精通'),
    ]
    
    skill_level = models.CharField(
        max_length=20,
        choices=SKILL_LEVEL_CHOICES,
        default='beginner',
        verbose_name="技能水平"
    )

    # 2. 技能标签（存储为字符串，如 "Python, Django, Vue"）
    skill_tags = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="技能标签"
    )

    # 3. 新增：头像字段
    # 注意：使用 ImageField 需要安装 Pillow 库 (pip install Pillow)
    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/', 
        default='avatars/default.png', 
        null=True, 
        blank=True, 
        verbose_name="个人头像"
    )

    # 4. 新增：个人简介
    bio = models.TextField(
        max_length=500, 
        blank=True, 
        verbose_name="个人简介"
    )

    # 5. 新增：昵称（如果你不想用系统默认的 username 展示在 Profile 页面）
    nickname = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name="昵称"
    )

    class Meta:
        verbose_name = "用户信息"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.nickname if self.nickname else self.username