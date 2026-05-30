from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse


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

    def test_register_page_status_code(self):
        """测试注册页面是否正常响应"""

        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
