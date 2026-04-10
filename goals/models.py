from django.db import models
from django.conf import settings

class LearningGoal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True) # 记得加上这个
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.title

    @property
    def progress(self):
        """核心逻辑：动态计算进度"""
        tasks = self.subtasks.all()
        total = tasks.count()
        if total == 0: return 0
        completed = tasks.filter(is_completed=True).count()
        return int((completed / total) * 100)

class SubTask(models.Model):
    # 建立外键关联
    goal = models.ForeignKey(LearningGoal, on_delete=models.CASCADE, related_name='subtasks')
    title = models.CharField(max_length=200)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.goal.title} - {self.title}"