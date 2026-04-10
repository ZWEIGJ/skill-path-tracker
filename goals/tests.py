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
    def test_delete_goal_logic(self):
        """测试用户删除自己的目标"""
        response = self.client.post(reverse('goal_delete', args=[self.goal.id]))
        # 验证重定向到看板
        self.assertEqual(response.status_code, 302)
        # 验证数据库中该目标已消失
        self.assertFalse(LearningGoal.objects.filter(id=self.goal.id).exists())

    def test_delete_goal_security(self):
        """测试越权删除：Bob 不能删除 Amy 的目标"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        # 创建另一个用户 Bob
        bob = User.objects.create_user(username='bob', password='Password123!')
        self.client.login(username='bob', password='Password123!')
        
        # Bob 尝试删除 Amy 的目标 (self.goal)
        response = self.client.post(reverse('goal_delete', args=[self.goal.id]))
        
        # 预期结果：应该返回 404，且目标依然存在于数据库
        self.assertEqual(response.status_code, 404)
        self.assertTrue(LearningGoal.objects.filter(id=self.goal.id).exists())