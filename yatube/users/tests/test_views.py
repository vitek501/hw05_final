from django.contrib.auth import get_user_model
from django.urls import reverse
from django import forms
from django.contrib.auth.forms import UsernameField
from django.test import TestCase, Client


User = get_user_model()


class UserURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            first_name='Boris',
            last_name='"The Blade"',
            username='Boris "The Blade"',
            password='secret')

    def setUp(self):
        self.guest_client = Client()
        self.client_boris = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.client_boris.login(first_name='Boris',
                                last_name='"The Blade"',
                                username='Boris "The Blade"',
                                password='secret',
                                email='boris@example.com'
                                )

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответсвующий шаблон."""
        templates_pages_names = {
            reverse('users:login'): 'users/login.html',
            reverse('users:signup'): 'users/signup.html',
            reverse('users:logout'): 'users/logged_out.html',
            reverse('users:password_reset_form'):
                'users/password_reset_form.html',
            reverse('users:password_reset_done'):
                'users/password_reset_done.html',
            reverse('users:password_rest_complete'):
                'users/password_reset_complete.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

        response = self.client_boris.get(reverse('users:password_change_form'))
        self.assertTemplateUsed(response, 'users/password_change_form.html')
        response = self.client_boris.get(reverse('users:password_change_done'))
        self.assertTemplateUsed(response, 'users/password_change_done.html')

    def test_signup_page_show_correct_context(self):
        """Шаблон signup сформирован с правильным контекстом."""
        response = self.authorized_client.post(
            reverse('users:signup')
        )
        form_fields = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': UsernameField,
            'email': forms.fields.EmailField,
            'password1': forms.fields.CharField,
            'password2': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
