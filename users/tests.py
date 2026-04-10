from django.test import TestCase
from django.contrib.auth import get_user_model

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