from django.db import models
from django.conf import settings
from django.utils import timezone

class LearningGoal(models.Model):
    """
    大目标模型：
    核心变更：增加了优先级和截止日期字段，并提供了动态属性判断进度和是否逾期。
    """
    # 优先级选项定义
    class Priority(models.TextChoices):
        LOW = 'L', '低'
        MEDIUM = 'M', '中'
        HIGH = 'H', '高'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # --- Step 5.1 新增字段 ---
    deadline = models.DateField(null=True, blank=True) # 截止日期
    priority = models.CharField(
        max_length=1,
        choices=Priority.choices,
        default=Priority.MEDIUM, # 默认中等
    )

    @property
    def progress(self):
        """核心逻辑：动态计算子任务完成百分比"""
        tasks = self.subtasks.all()
        total = tasks.count()
        if total == 0:
            return 0
        completed = tasks.filter(is_completed=True).count()
        return int((completed / total) * 100)

    @property
    def is_overdue(self):
        """
        判断是否逾期：
        1. 必须设置了截止日期
        2. 截止日期早于今天
        3. 进度未达到 100%
        """
        if self.deadline and self.deadline < timezone.now().date() and self.progress < 100:
            return True
        return False

    def __str__(self):
        return self.title


class SubTask(models.Model):
    """
    子任务模型：
    通过 ForeignKey 与 LearningGoal 建立一对多关联。
    """
    goal = models.ForeignKey(
        LearningGoal, 
        on_delete=models.CASCADE, 
        related_name='subtasks'
    )
    title = models.CharField(max_length=200)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # 用于统计完成时间

    def __str__(self):
        return f"{self.goal.title} - {self.title}"