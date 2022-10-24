import shutil
import tempfile
from django.contrib.auth import get_user_model
from django.urls import reverse
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.core.cache import cache
from django.conf import settings

from posts.models import Post, Group

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            first_name='Boris',
            last_name='"The Blade"',
            username='Boris "The Blade"',
            password='secret')
        cls.test_group = Group.objects.create(
            title='группа',
            description='описание группы',
            slug='test-slug')
        cls.post = Post.objects.create(
            text='Текст',
            author=cls.user,
            group=cls.test_group,
            image=cls.__test_image(),
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    @staticmethod
    def __test_image():
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
        return uploaded 

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответсвующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.test_group.slug}):
                        'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.user.username}):
                        'posts/profile.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}):
                        'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template, f'Тест {template}')

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        image_0 = first_object.image
        second_object = response.context['title']
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_author_0, self.post.author)
        self.assertEqual(post_group_0, self.test_group)
        self.assertEqual(image_0, self.post.image)
        self.assertEqual(second_object, 'Последние обновления на сайте')

    def test_group_posts_page_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.test_group.slug})
        )
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        image_0 = first_object.image
        second_object = response.context['title']
        third_object = response.context['group']
        group_title_0 = third_object.title
        group_slug_0 = third_object.slug
        group_description_0 = third_object.description
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_author_0, self.user)
        self.assertEqual(post_group_0, self.test_group)
        self.assertEqual(image_0, self.post.image)
        self.assertEqual(second_object, f'Записи сообщества {third_object}')
        self.assertEqual(group_title_0, self.test_group.title)
        self.assertEqual(group_slug_0, self.test_group.slug)
        self.assertEqual(group_description_0, self.test_group.description)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        image_0 = first_object.image
        second_object = response.context['title']
        third_object = response.context['author']
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_author_0, self.user)
        self.assertEqual(post_group_0, self.test_group)
        self.assertEqual(image_0, self.post.image)
        self.assertEqual(second_object,
                         f'{self.post.author} профайл пользователя')
        self.assertEqual(third_object, self.user)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        SYMBOLS_COUNT = slice(None, 30)
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        first_object = response.context['post']
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        image_0 = first_object.image
        second_object = response.context['title']
        third_object = response.context['posts_count']
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_author_0, self.user)
        self.assertEqual(post_group_0, self.test_group)
        self.assertEqual(image_0, self.post.image)
        self.assertEqual(
            second_object,
            'Пост ' + self.post.text[SYMBOLS_COUNT])
        self.assertEqual(third_object, self.post.id)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.post(
            reverse('posts:post_create')
        )
        first_object = response.context['title']
        self.assertEqual(first_object, 'Новый пост')
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        first_object = response.context['title']
        second_object = response.context['is_edit']
        third_object = response.context['post']
        self.assertEqual(first_object, 'Редактировать пост')
        self.assertEqual(second_object, True)
        self.assertEqual(third_object, self.post)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_initial_value(self):
        """Предустановленнное значение формы."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        text_label = response.context['form'].fields['text'].label
        text_help_text = response.context['form'].fields['text'].help_text
        group_label = response.context['form'].fields['group'].label
        group_help_text = response.context['form'].fields['group'].help_text
        self.assertEqual(text_label, 'Текст поста')
        self.assertEqual(text_help_text, 'Текст нового поста')
        self.assertEqual(group_label, 'Группа')
        self.assertEqual(group_help_text,
                         'Группа, к которой будет относиться пост')

    def test_cache_index(self):
        """Проверка хранения и очистки кэша для index."""
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='test_cache',
            author=self.user,
        )
        response_old = self.authorized_client.get(reverse('posts:index'))
        old_posts = response_old.content
        self.assertEqual(old_posts, posts)
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user_boris = User.objects.create_user(username='Boris "The Blade"')
        cls.user_mickey = User.objects.create_user(username="Mickey O'Neil")
        cls.test_group = Group.objects.create(
            title='группа',
            description='описание группы',
            slug='test-slug')
        cls.test_group_2 = Group.objects.create(
            title='группа 2',
            description='описание группы 2',
            slug='test-slug2')
        NUMBER_OF_POSTS = 15
        for post in range(NUMBER_OF_POSTS):
            if post < 13:
                Post.objects.create(text=f'Текст {post}',
                                    author=cls.user_boris,
                                    group=cls.test_group)
            else:
                Post.objects.create(text=f'Текст {post}',
                                    author=cls.user_mickey,
                                    group=cls.test_group_2)

    def setUp(self):
        self.guest_client = Client()
        cache.clear()

    def test_page_contains_ten_records(self):
        """Первая стариница содержит 10 постов, вторая страница 3 поста"""
        FIRST_POST_COUNT = 10

        reverse_page_names = {
            reverse('posts:index'): 5,
            reverse('posts:group_list',
                    kwargs={'slug': self.test_group.slug}): 3,
            reverse('posts:profile',
                    kwargs={'username': self.user_boris.username}): 3,
        }
        for reverse_name, second_post_count in reverse_page_names.items():
            with self.subTest():
                response = self.guest_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']),
                                 FIRST_POST_COUNT)
                response = self.guest_client.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context['page_obj']),
                                 second_post_count)

    def test_added_post_show_correct_pages(self):
        """Пост добавлен на первую страницу и отсутствует в другой группе"""
        new_post = Post.objects.create(
            text='Буквы',
            author=self.user_mickey,
            group=self.test_group_2
        )
        reverse_page_names = [
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': self.test_group_2.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.user_mickey.username}),
        ]

        for reverse_name in reverse_page_names:
            response = self.guest_client.get(reverse_name)
            posts = response.context['page_obj'][0]
            self.assertEqual(posts, new_post)
        dif_group = self.test_group.grouped_posts.all()
        self.assertNotIn(new_post, dif_group)
