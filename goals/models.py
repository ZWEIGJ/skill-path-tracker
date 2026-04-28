from django.db import models
from django.conf import settings
from django.utils import timezone

class Tag(models.Model):
    """
    标签模型：支持用户自定义分类。
    """
    name = models.CharField(max_length=30, verbose_name="标签名")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="所属用户")
    color = models.CharField(
        max_length=20, 
        default='#e3e2e0', 
        null=True, 
        blank=True, 
        verbose_name="标签颜色"
    )

    class Meta:
        unique_together = ['name', 'user']
        verbose_name = "分类标签"
        verbose_name_plural = "分类标签"

    def __str__(self):
        return self.name

class LearningGoal(models.Model):
    """
    学习目标模型：支持进度计算、逾期判定和标签关联。
    """
    class Priority(models.TextChoices):
        LOW = 'L', '低'
        MEDIUM = 'M', '中'
        HIGH = 'H', '高'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, verbose_name="目标标题")
    description = models.TextField(blank=True, null=True, verbose_name="目标描述")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    deadline = models.DateField(null=True, blank=True, verbose_name="截止日期")
    priority = models.CharField(
        max_length=1,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        verbose_name="优先级"
    )
    
    is_completed = models.BooleanField(default=False, verbose_name="是否达成")
    is_archived = models.BooleanField(default=False, verbose_name="是否归档")
    
    # 🌟 核心修复：记录归档的具体时间，用于统计“本周突破”
    archived_at = models.DateTimeField(null=True, blank=True, verbose_name="归档时间")
    
    tags = models.ManyToManyField(Tag, blank=True, related_name='goals', verbose_name="分类标签")

    @property
    def progress(self):
        """动态计算进度百分比"""
        tasks = self.subtasks.all()
        total = tasks.count()
        if total == 0: return 0
        completed = tasks.filter(is_completed=True).count()
        return int((completed / total) * 100)

    def update_completion_status(self):
        """检查子任务，如果全部完成则标记 is_completed 为 True"""
        tasks = self.subtasks.all()
        if tasks.exists() and all(t.is_completed for t in tasks):
            self.is_completed = True
        else:
            self.is_completed = False
        self.save(update_fields=['is_completed'])

    @property
    def is_overdue(self):
        """逾期判定"""
        if self.deadline and self.deadline < timezone.now().date() and not self.is_completed:
            return True
        return False

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "学习目标"
        verbose_name_plural = "学习目标"

class SubTask(models.Model):
    """
    子任务模型。
    """
    goal = models.ForeignKey(LearningGoal, on_delete=models.CASCADE, related_name='subtasks')
    title = models.CharField(max_length=200, verbose_name="任务内容")
    is_completed = models.BooleanField(default=False, verbose_name="是否完成")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    def save(self, *args, **kwargs):
        # 每次子任务保存时，触发父目标的完成状态检查
        super().save(*args, **kwargs)
        self.goal.update_completion_status()

    def delete(self, *args, **kwargs):
        # 删除子任务时也要重新检查状态
        goal = self.goal
        super().delete(*args, **kwargs)
        goal.update_completion_status()

    def __str__(self):
        return f"{self.goal.title} - {self.title}"

    class Meta:
        verbose_name = "子任务"
        verbose_name_plural = "子任务"