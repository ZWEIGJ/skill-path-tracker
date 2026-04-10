from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import LearningGoal

class GoalUpdateTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='amy', password='Password123!')
        self.client.login(username='amy', password='Password123!')
        self.goal = LearningGoal.objects.create(user=self.user, title="测试目标")

    def test_toggle_goal_status(self):
        """测试点击后状态反转"""
        # 发送请求到切换接口
        response = self.client.get(reverse('goal_toggle', args=[self.goal.id]))
        self.goal.refresh_from_db()
        self.assertTrue(self.goal.is_completed) # 初始是False，点击后应为True
        
        # 再次点击
        self.client.get(reverse('goal_toggle', args=[self.goal.id]))
        self.goal.refresh_from_db()
        self.assertFalse(self.goal.is_completed) # 应变回False