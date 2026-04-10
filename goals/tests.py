import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import LearningGoal

User = get_user_model()

class GoalProgressTest(TestCase):
    def setUp(self):
        """每个测试开始前都会运行，准备测试环境"""
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client.login(username='testuser', password='password123')

    def test_progress_calculation(self):
        """测试看板的进度计算逻辑 (Step 3.1)"""
        # 初始状态进度为 0
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.context['progress_percentage'], 0)

        # 增加两个目标，一个完成，一个未完成
        LearningGoal.objects.create(user=self.user, title="Goal 1", is_completed=True)
        LearningGoal.objects.create(user=self.user, title="Goal 2", is_completed=False)
        
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.context['progress_percentage'], 50)

    def test_ajax_toggle_goal(self):
        """测试异步切换目标状态 (Step 3.2)"""
        # 创建一个初始未完成的目标
        goal = LearningGoal.objects.create(user=self.user, title="AJAX Test", is_completed=False)
        url = reverse('goal_toggle', args=[goal.pk])
        
        # 发送一个模拟的 AJAX 请求 (包含 XMLHttpRequest 头)
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        # 1. 验证 HTTP 状态码是否为 200 (成功)
        self.assertEqual(response.status_code, 200)
        
        # 2. 解析返回的 JSON 数据
        data = json.loads(response.content)
        
        # 3. 验证 JSON 里的数据是否符合预期
        self.assertTrue(data['is_completed']) # 应该从 False 变成 True
        self.assertEqual(data['progress_percentage'], 100) # 因为只有这一个目标且完成了
        self.assertEqual(data['status'], 'success')