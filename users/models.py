from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # 定义技能等级选项 [cite: 14, 29]
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
    skill_tags = models.CharField(max_length=255, blank=True, verbose_name="技能标签")