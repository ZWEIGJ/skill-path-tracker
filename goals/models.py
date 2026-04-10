from django.db import models
from django.conf import settings

class LearningGoal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, verbose_name="学习目标")
    description = models.TextField(blank=True, verbose_name="目标详情")
    created_at = models.DateTimeField(auto_now_add=True)
    # --- 新增字段 ---
    is_completed = models.BooleanField(default=False, verbose_name="是否完成")

    def __str__(self):
        return self.title