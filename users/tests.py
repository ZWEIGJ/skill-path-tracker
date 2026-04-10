from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

class UserModelTest(TestCase):
    def test_create_user_with_skill_level(self):
        """测试创建用户时是否能保存技能等级"""
        User = get_user_model()
        user = User.objects.create_user(
            username='testuser',
            password='password123',
            skill_level='beginner' # 预期有的字段
        )
        self.assertEqual(user.skill_level, 'beginner')

class UserRegistrationTest(TestCase):
    def test_registration_view_status_code(self):
        """测试注册页面是否能正常打开"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        
    def test_user_registration_logic(self):
            """测试用户是否能通过表单成功注册并保存技能等级"""
            data = {
                'username': 'newuser',
                'password1': 'Password123!',  # 修改为 password1
                'password2': 'Password123!',  # 修改为 password2
                'skill_level': 'intermediate',
                'skill_tags': 'Python'
            }
            self.client.post(reverse('register'), data)
            
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(username='newuser')
            self.assertEqual(user.skill_level, 'intermediate')