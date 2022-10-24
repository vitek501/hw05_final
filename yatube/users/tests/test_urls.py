from django.contrib.auth import get_user_model
from http import HTTPStatus
from django.test import TestCase, Client

User = get_user_model()


class StaticPagesURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            first_name='Boris',
            last_name='"The Blade"',
            username='Boris "The Blade"',
            password='Secret534')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.client_boris = Client()
        self.authorized_client.force_login(self.user)
        self.client_boris.login(
            username='Boris "The Blade"',
            password='Secret534'
        )

    def test_users_url_exists_at_desired_location(self):
        """Проверка доступности адреса и шаблона для страниц"""
        templates_url_names = {
            '/auth/logout/': 'users/logged_out.html',
            '/auth/signup/': 'users/signup.html',
            '/auth/password_reset/': 'users/password_reset_form.html',
            '/auth/password_reset/done/': 'users/password_reset_done.html',
            '/auth/reset/done/': 'users/password_reset_complete.html'
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code,
                                 HTTPStatus.OK)
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response,
                                        template)

        response = self.client_boris.get('/auth/password_change/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'users/password_change_form.html')

        response = self.client_boris.get('/auth/password_change/done/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'users/password_change_done.html')
