from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import LearningGoal, SubTask

User = get_user_model()


class GoalHierarchyTest(TestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            username='tester',
            password='password123'
        )

        self.client = Client()

        self.client.login(
            username='tester',
            password='password123'
        )

        # 创建测试目标
        self.goal = LearningGoal.objects.create(
            user=self.user,
            title='测试大目标'
        )

    def test_goal_list_view(self):
        """测试目标列表页面是否正常加载"""

        response = self.client.get(reverse('goal_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '测试大目标')

    def test_subtask_creation_and_progress(self):
        """测试子任务创建与目标进度联动"""

        # 初始进度
        self.assertEqual(self.goal.progress, 0)

        # AJAX 创建子任务
        url = reverse('subtask_add', args=[self.goal.id])

        response = self.client.post(
            url,
            {'content': '完成 ORM 学习'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 200)

        # 获取子任务
        subtask = SubTask.objects.first()

        # 切换任务状态
        toggle_url = reverse('subtask_toggle', args=[subtask.id])

        self.client.get(
            toggle_url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # 刷新目标对象
        self.goal.refresh_from_db()

        # 当前仅有一个任务，因此进度应为100%
        self.assertEqual(self.goal.progress, 100)

    def test_security_access(self):
        """测试用户不能操作其他人的任务"""

        other_user = User.objects.create_user(
            username='other',
            password='password'
        )

        other_goal = LearningGoal.objects.create(
            user=other_user,
            title='他人目标'
        )

        other_task = SubTask.objects.create(
            goal=other_goal,
            content='他人任务'
        )

        # 尝试修改其他用户任务
        url = reverse('subtask_toggle', args=[other_task.id])

        response = self.client.get(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # get_object_or_404 应返回 404
        self.assertEqual(response.status_code, 404)
