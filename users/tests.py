from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import LearningGoal, SubTask, Tag, CustomPathNode


class UserAuthenticationTest(TestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='Password123!'
        )

    def test_login_page_status_code(self):
        """测试登录页面是否正常响应"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_user_login(self):
        """测试用户是否能够正常登录"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'Password123!'
        })

        self.assertEqual(response.status_code, 302)


class LearningGoalModelTest(TestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username='goaluser',
            password='Password123!'
        )

    def test_create_learning_goal(self):
        """测试学习目标是否创建成功"""

        goal = LearningGoal.objects.create(
            user=self.user,
            title='掌握 Python 基础语法',
            priority='high'
        )

        self.assertEqual(goal.title, '掌握 Python 基础语法')
        self.assertEqual(goal.user.username, 'goaluser')


class SubTaskModelTest(TestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username='taskuser',
            password='Password123!'
        )

        self.goal = LearningGoal.objects.create(
            user=self.user,
            title='学习 Django'
        )

    def test_subtask_completion_status(self):
        """测试子任务完成状态是否能够更新"""

        subtask = SubTask.objects.create(
            goal=self.goal,
            content='完成 ORM 学习',
            is_completed=False
        )

        subtask.is_completed = True
        subtask.save()

        self.assertTrue(subtask.is_completed)


class TagRelationshipTest(TestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username='taguser',
            password='Password123!'
        )

    def test_goal_tag_relationship(self):
        """测试学习目标与标签的关联关系"""

        goal = LearningGoal.objects.create(
            user=self.user,
            title='前端开发学习'
        )

        tag = Tag.objects.create(
            name='JavaScript',
            color='#FFD43B'
        )

        goal.tags.add(tag)

        self.assertEqual(goal.tags.count(), 1)


class CustomPathNodeTest(TestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username='pathuser',
            password='Password123!'
        )

    def test_create_custom_path_node(self):
        """测试多泳道路径节点是否创建成功"""

        node = CustomPathNode.objects.create(
            user=self.user,
            path_name='后端开发',
            milestone_name='学习 Django ORM',
            order_index=1
        )

        self.assertEqual(node.path_name, '后端开发')
        self.assertEqual(node.order_index, 1)

