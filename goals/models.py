from django.db import models
from django.conf import settings
from django.utils import timezone

class LearningGoal(models.Model):
    """
    大目标模型：
    核心功能：支持优先级排序、截止日期、动态进度计算、逾期判定以及归档管理。
    """
    # 优先级选项定义
    class Priority(models.TextChoices):
        LOW = 'L', '低'
        MEDIUM = 'M', '中'
        HIGH = 'H', '高'

    # 基础字段
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, verbose_name="目标标题")
    description = models.TextField(blank=True, null=True, verbose_name="目标描述")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    # 扩展字段 (Step 5.1 & 6.3)
    deadline = models.DateField(null=True, blank=True, verbose_name="截止日期")
    priority = models.CharField(
        max_length=1,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        verbose_name="优先级"
    )
    is_archived = models.BooleanField(default=False, verbose_name="是否归档")

    @property
    def progress(self):
        """
        核心逻辑：动态计算子任务完成百分比。
        不需要存储到数据库，每次访问时实时根据子任务状态计算。
        """
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
        条件：设置了日期、日期已过、且进度未满 100%。
        """
        if self.deadline and self.deadline < timezone.now().date() and self.progress < 100:
            return True
        return False

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "学习目标"
        verbose_name_plural = "学习目标"


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
    title = models.CharField(max_length=200, verbose_name="任务内容")
    is_completed = models.BooleanField(default=False, verbose_name="是否完成")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间") # 用于趋势图统计

    def __str__(self):
        return f"{self.goal.title} - {self.title}"

    class Meta:
        verbose_name = "子任务"
        verbose_name_plural = "子任务"