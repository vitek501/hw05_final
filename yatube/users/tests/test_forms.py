from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase, Client


User = get_user_model()


class UserCreateFormTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_create_user(self):
        """Валидная форма создает запись в User."""
        posts_count = User.objects.count()
        form_data = {
            'first_name': 'Boris',
            'last_name': 'The_Blade',
            'username': 'Boris_The_Blade',
            'email': 'boris@example.com',
            'password1': 'Secret345"',
            'password2': 'Secret345"',
        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(User.objects.count(), posts_count + 1)
        self.assertTrue(
            User.objects.filter(
                username='Boris_The_Blade',
            ).exists()
        )
