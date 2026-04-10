from django.test import TestCase
from django.contrib.auth import get_user_model  # 修改这里：动态获取当前激活的用户模型
from .models import LearningGoal
from django.urls import reverse

User = get_user_model()  # 获取你自定义的 CustomUser

class GoalProgressTest(TestCase):
    def setUp(self):
        # 这里的代码现在会自动使用你的 CustomUser
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client.login(username='testuser', password='password123')

    def test_progress_calculation(self):
        """测试看板的进度计算逻辑"""
        # 1. 初始状态：0个目标
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.context['progress_percentage'], 0)

        # 2. 增加两个目标，一个完成，一个未完成
        LearningGoal.objects.create(user=self.user, title="Goal 1", is_completed=True)
        LearningGoal.objects.create(user=self.user, title="Goal 2", is_completed=False)
        
        # 再次请求页面
        response = self.client.get(reverse('dashboard'))
        
        # 验证计算结果
        self.assertEqual(response.context['progress_percentage'], 50)
        self.assertEqual(response.context['total_goals'], 2)
        self.assertEqual(response.context['completed_goals'], 1)