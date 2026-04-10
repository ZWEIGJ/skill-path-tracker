from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import LearningGoal, SubTask

User = get_user_model()

class GoalHierarchyTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='password123')
        self.client = Client()
        self.client.login(username='tester', password='password123')
        # 创建一个初始大目标
        self.goal = LearningGoal.objects.create(user=self.user, title="测试大目标")

    def test_goal_list_view(self):
        """测试大目标列表页"""
        response = self.client.get(reverse('goal_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "测试大目标")

    def test_subtask_creation_and_progress(self):
        """测试子任务创建及大目标进度联动"""
        # 1. 初始进度应为 0
        self.assertEqual(self.goal.progress, 0)

        # 2. 模拟 AJAX 添加一个子任务
        url = reverse('subtask_add', args=[self.goal.id])
        response = self.client.post(url, {'title': '子任务1'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        
        # 3. 切换子任务状态
        subtask = SubTask.objects.first()
        toggle_url = reverse('subtask_toggle', args=[subtask.id])
        self.client.get(toggle_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        # 4. 验证进度是否变为 100% (因为目前只有一个任务且已完成)
        self.assertEqual(self.goal.progress, 100)

    def test_security_access(self):
        """测试越权访问：用户不能操作他人的子任务"""
        other_user = User.objects.create_user(username='other', password='password')
        other_goal = LearningGoal.objects.create(user=other_user, title="他人目标")
        other_task = SubTask.objects.create(goal=other_goal, title="他人任务")
        
        # 尝试切换他人任务状态
        url = reverse('subtask_toggle', args=[other_task.id])
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        # 应该是 404，因为 views.py 里的 get_object_or_404 限制了 user
        self.assertEqual(response.status_code, 404)