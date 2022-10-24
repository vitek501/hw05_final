import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.core.cache import cache

from http import HTTPStatus
from posts.models import Post, Group, Comment, Follow
from posts.forms import PostForm


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='Boris_The_Blade',
        )
        cls.user_mickey = User.objects.create_user(username='Mickey')
        cls.user_bob = User.objects.create_user(username='Bob')
        cls.test_group = Group.objects.create(
            title='группа',
            description='описание группы',
            slug='test-slug')
        cls.post = Post.objects.create(
            text='Текст',
            author=cls.user,
            group=cls.test_group,
        )
        cls.form = PostForm()
        cls.URL_EDIT = reverse(
            'posts:post_edit',
            kwargs={'post_id': cls.post.id}
        )
        cls.URL_POST_DETAIL = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.id}
        )
        cls.URL_ADD_COMMENT = reverse(
            'posts:add_comment',
            kwargs={'post_id': cls.post.id}
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.client_micky = Client()
        self.client_micky.force_login(self.user_mickey)
        self.client_bob = Client()
        self.client_bob.force_login(self.user_bob)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        small_jpg = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.jpg',
            content=small_jpg,
            content_type='image/jpg'
        )
        form_data = {
            'text': ('Пять минут назад ты сказал, '
                     'что будет готово через две минуты!'),
            'group': self.test_group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group'],
                image='posts/small.jpg',
                author=self.user).exists()
        )

    def test_cant_create_not_authorized(self):
        """Не авторизованный пользователь не может создать запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': ('Пять минут назад ты сказал, '
                     'что будет готово через две минуты!'),
            'group': self.test_group.id,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        url_redirect = (f"{reverse('users:login')}"
                        f"?next={reverse('posts:post_create')}")
        self.assertRedirects(response, url_redirect)
        self.assertEqual(Post.objects.count(), posts_count)

    def test_cant_create_empty_text(self):
        """Не валидная форма не создает запись"""
        posts_count = Post.objects.count()
        form_data = {
            'text': '',
            'slug': self.test_group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFormError(
            response,
            'form',
            'text',
            'Обязательное поле.'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_label(self):
        """Проверка label формы Post."""
        text_label = self.form.fields['text'].label
        group_label = self.form.fields['group'].label
        self.assertEqual(text_label, 'Текст поста')
        self.assertEqual(group_label, 'Группа')

    def test_help_text(self):
        """Проверка help text формы Post"""
        text_help_text = self.form.fields['text'].help_text
        group_help_text = self.form.fields['group'].help_text
        self.assertEqual(text_help_text, 'Текст нового поста')
        self.assertEqual(group_help_text,
                         'Группа, к которой будет относиться пост')

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': ('Очень эффективно, Тони… '
                     'Не очень деликатно, но ОЧЕНЬ эффективно!'),
        }
        response = self.authorized_client.post(
            self.URL_EDIT,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.URL_POST_DETAIL)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
            ).exists()
        )

    def test_cant_edit_empty_text(self):
        """Не валидная форма не редактирует запись в Post"""
        posts_count = Post.objects.count()
        form_data = {
            'text': '',
        }
        response = self.authorized_client.post(
            self.URL_EDIT,
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFormError(
            response,
            'form',
            'text',
            'Обязательное поле.'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_cant_edit_not_authorized(self):
        """Не авторизованный пользователь не может редактировать Post"""
        posts_count = Post.objects.count()
        form_data = {
            'text': ('Очень эффективно, Тони… '
                     'Не очень деликатно, но ОЧЕНЬ эффективно!'),
        }
        response = self.guest_client.post(
            self.URL_EDIT,
            data=form_data,
            follow=True
        )
        redirect_url = (f"{reverse('users:login')}"
                        f"?next={self.URL_EDIT}")
        self.assertRedirects(response, redirect_url)
        self.assertEqual(Post.objects.count(), posts_count)
        self.post.refresh_from_db()
        self.assertNotEqual(self.post.text, form_data['text'])

    def test_cant_edit_not_author(self):
        """Не автор не может редактировать Post"""
        posts_count = Post.objects.count()
        form_data = {
            'text': ('Очень эффективно, Тони… '
                     'Не очень деликатно, но ОЧЕНЬ эффективно!'),
        }
        response = self.client_micky.post(
            self.URL_EDIT,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.URL_POST_DETAIL)
        self.assertEqual(Post.objects.count(), posts_count)
        self.post.refresh_from_db()
        self.assertNotEqual(self.post.text, form_data['text'])

    def test_comment_post(self):
        """Создается комментарий к Post"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Нравятся пёсики?'
        }
        response = self.authorized_client.post(
            self.URL_ADD_COMMENT,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.URL_POST_DETAIL)
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                post=self.post,
                text=form_data['text'],
            ).exists()
        )

    def test_comment_post_not_authorized(self):
        """Не авторизованный пользователь не может комментировать Post"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Да, пёсики, нравятся пёсики?'
        }
        response = self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        redirect_url = (
            f"{reverse('users:login')}"
            f"?next={self.URL_ADD_COMMENT}")
        self.assertRedirects(response, redirect_url)
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertFalse(
            Comment.objects.filter(
                post=self.post,
                text=form_data['text'],
            ).exists()
        )

    def test_comment_post_not_validate(self):
        """Не валидная форма не создает комментарий"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': '',
        }
        response = self.authorized_client.post(
            self.URL_POST_DETAIL,
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertFormError(
            response,
            'form',
            'text',
            'Обязательное поле.'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_follow_post_not_authorized(self):
        """Не авторизованный пользователь не может подписаться на автора"""
        follows_count = Follow.objects.count()
        self.guest_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_mickey}),
            follow=True
        )
        self.assertEqual(Follow.objects.count(), follows_count)

    def test_follow_post_authorized(self):
        """Авторизованный пользователь может подписаться на автора
        и отписаться"""
        follows_count = Follow.objects.count()
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_mickey}),
            follow=True
        )
        self.assertEqual(Follow.objects.count(), follows_count + 1)
        self.authorized_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user_mickey}),
            follow=True
        )
        self.assertEqual(Follow.objects.count(), follows_count)

    def test_follow_post(self):
        """Новая запись появляется в ленте тех, кто подписан"""
        self.client_micky.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user}),
            follow=True
        )
        post = Post.objects.create(
            text='Уникальный контент',
            author=self.user,
            group=self.test_group,
        )
        response = self.client_micky.get(reverse(
            'posts:follow_index'),
        )
        self.assertContains(response, post.text)
        cache.clear()
        response_bob = self.client_bob.get(
            reverse('posts:follow_index'),
            follow=True
        )
        self.assertNotContains(response_bob, post.text)
