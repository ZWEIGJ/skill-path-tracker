import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import LearningGoal

User = get_user_model()

class GoalProgressTest(TestCase):
    def setUp(self):
        """测试前的环境准备"""
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client.login(username='testuser', password='password123')

    def test_progress_calculation(self):
        """测试看板的进度计算逻辑 (Step 3.1)"""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.context['progress_percentage'], 0)

        LearningGoal.objects.create(user=self.user, title="Goal 1", is_completed=True)
        LearningGoal.objects.create(user=self.user, title="Goal 2", is_completed=False)
        
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.context['progress_percentage'], 50)

    def test_ajax_toggle_goal(self):
        """测试异步切换目标状态 (Step 3.2)"""
        goal = LearningGoal.objects.create(user=self.user, title="AJAX Test", is_completed=False)
        url = reverse('goal_toggle', args=[goal.pk])
        
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['is_completed'])
        self.assertEqual(data['status'], 'success')

    def test_ajax_delete_goal(self):
        """测试异步删除目标 (Step 3.3)"""
        # 注意：这里前面必须有 4 个空格缩进，使其属于 GoalProgressTest 类
        goal = LearningGoal.objects.create(user=self.user, title="Delete Me")
        url = reverse('goal_delete', args=[goal.pk])
        
        # 发送 AJAX POST 请求
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        # 验证返回
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        
        # 验证数据库里已经删除了
        self.assertFalse(LearningGoal.objects.filter(pk=goal.pk).exists())