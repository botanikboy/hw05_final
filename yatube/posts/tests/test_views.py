import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.core.cache import cache

from posts.models import Post, Group, User, Follow
from posts.constants import POSTS_COUNT


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostsTemplateTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост на много символов, '
            'чтобы проверить длину вывода метода str().',
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(User.objects.get(username='auth'))
        cache.clear()

    def test_pages_uses_correct_template(self):
        names_templates_pages = {
            reverse('posts:index'):
                'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'auth'}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': 1}):
                'posts/post_detail.html',
            reverse('posts:post_create'):
                'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': 1}):
                'posts/create_post.html',
        }
        for reverse_name, template in names_templates_pages.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user_1,
            text='Тестовый пост с группой и картинкой',
            group=cls.group,
            image=cls.image,
        )

        cls.user_2 = User.objects.create_user(username='second_auth')
        cls.post = Post.objects.create(
            author=cls.user_2,
            text='Тестовый пост без группы',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_1)
        cache.clear()

    def test_index_page_show_correct_context(self):
        response = self.client.get(reverse('posts:index'))
        first_post_on_page = response.context.get('page_obj')[0]
        self.assertIsInstance(first_post_on_page, Post)

        post_text_0 = first_post_on_page.text
        post_author_0 = first_post_on_page.author.username
        self.assertEqual(post_text_0, 'Тестовый пост без группы')
        self.assertEqual(post_author_0, 'second_auth')

        post_image_1 = response.context.get('page_obj')[1].image
        self.assertEqual(post_image_1.read(), self.small_gif)

    def test_group_list_page_show_correct_context(self):
        response = self.client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'})
        )
        first_post_on_page = response.context.get('page_obj')[0]
        self.assertIsInstance(first_post_on_page, Post)

        post_text_0 = first_post_on_page.text
        post_author_0 = first_post_on_page.author.username
        post_group_0 = first_post_on_page.group.title
        post_image_0 = first_post_on_page.image

        self.assertEqual(post_text_0, 'Тестовый пост с группой и картинкой')
        self.assertEqual(post_author_0, 'auth')
        self.assertEqual(post_group_0, 'Тестовая группа')
        self.assertEqual(post_image_0.read(), self.small_gif)

    def test_profile_page_show_correct_context(self):
        response = self.client.get(
            reverse('posts:profile', kwargs={'username': 'auth'})
        )
        first_post_on_page = response.context.get('page_obj')[0]
        self.assertIsInstance(first_post_on_page, Post)

        post_text_0 = first_post_on_page.text
        post_author_0 = first_post_on_page.author.username
        post_group_0 = first_post_on_page.group.title
        post_image_0 = first_post_on_page.image

        self.assertEqual(post_text_0, 'Тестовый пост с группой и картинкой')
        self.assertEqual(post_author_0, 'auth')
        self.assertEqual(post_group_0, 'Тестовая группа')
        self.assertEqual(post_image_0.read(), self.small_gif)

    def test_post_detail_page_show_correct_context(self):
        response = self.client.get(
            reverse('posts:post_detail', kwargs={'post_id': 1})
        )
        post_on_page = response.context.get('post')
        self.assertIsInstance(post_on_page, Post)

        post_text = post_on_page.text
        post_author = post_on_page.author.username
        post_group = post_on_page.group.title
        post_image = post_on_page.image

        self.assertEqual(post_text, 'Тестовый пост с группой и картинкой')
        self.assertEqual(post_author, 'auth')
        self.assertEqual(post_group, 'Тестовая группа')
        self.assertEqual(post_image.read(), self.small_gif)

    def test_post_create_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }

        for field, field_type in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, field_type)

    def test_post_edit_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': 1})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }

        for field, field_type in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, field_type)

        self.assertEqual(
            response.context.get('form')['text'].value(),
            'Тестовый пост с группой и картинкой'
        )

        self.assertEqual(
            response.context.get('form')['group'].value(),
            1
        )

    def test_index_page_cache(self):
        response = self.client.get(reverse('posts:index'))
        page_initial = response.content
        Post.objects.create(
            author=self.user_1,
            text='Totaly new post!',
        )
        response = self.client.get(reverse('posts:index'))
        page_after_adding_post = response.content
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        page_cleared_cache = response.content

        self.assertEqual(page_initial, page_after_adding_post)
        self.assertNotEqual(page_initial, page_cleared_cache)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        Post.objects.bulk_create(
            [
                Post(
                    author=cls.user,
                    text=f'Тестовый пост на много символов. Номер поста {i}',
                    group=cls.group,
                ) for i in range(POSTS_COUNT + 3)
            ]
        )
        cache.clear()

    def test_pages_have_correct_posts_count(self):
        reverse_names_counts = {
            reverse('posts:index'):
                POSTS_COUNT,
            reverse('posts:index') + '?page=2':
                Post.objects.count() - POSTS_COUNT,
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}):
                POSTS_COUNT,
            reverse('posts:group_list',
                    kwargs={'slug': 'test-slug'}) + '?page=2':
                self.group.posts.count() - POSTS_COUNT,
            reverse('posts:profile', kwargs={'username': 'auth'}):
                POSTS_COUNT,
            reverse('posts:profile',
                    kwargs={'username': 'auth'}) + '?page=2':
                self.user.posts.count() - POSTS_COUNT,
        }

        for reverse_name, count in reverse_names_counts.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']), count
                )


class AuthorSubcribtionTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_1 = User.objects.create_user(username='first_auth')
        cls.post = Post.objects.create(
            author=cls.author_1,
            text='Тестовый пост первого автора',
        )
        cls.author_2 = User.objects.create_user(username='second_auth')
        cls.post = Post.objects.create(
            author=cls.author_2,
            text='Тестовый пост второго автора',
        )
        cls.user_1 = User.objects.create_user(username='user_1')
        cls.user_2 = User.objects.create_user(username='user_2')

    def setUp(self):
        self.authorized_client_1 = Client()
        self.authorized_client_1.force_login(self.user_1)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user_2)
        cache.clear()

    def test_user_can_follow_unfollow(self):
        self.authorized_client_1.get(
            reverse('posts:profile_follow', args=['first_auth'])
        )
        self.authorized_client_1.get(
            reverse('posts:profile_follow', args=['second_auth'])
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.user_1,
                author=self.author_1
            ).exists()
        )
        response = self.authorized_client_1.get(reverse('posts:follow_index'))
        first_post_on_page = response.context.get('page_obj')[0]
        self.assertEqual(
            first_post_on_page,
            Post.objects.filter(author=self.author_2).last()
        )
        self.authorized_client_1.get(
            reverse('posts:profile_unfollow', args=['second_auth'])
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.user_1,
                author=self.author_2
            ).exists()
        )
        response = self.authorized_client_1.get(reverse('posts:follow_index'))
        first_post_on_page = response.context.get('page_obj')[0]
        self.assertNotEqual(
            first_post_on_page,
            Post.objects.filter(author=self.author_2).last()
        )

    def test_new_post_in_follow(self):
        self.authorized_client_1.get(
            reverse('posts:profile_follow', args=['first_auth'])
        )
        self.authorized_client_1.get(
            reverse('posts:profile_follow', args=['second_auth'])
        )
        self.authorized_client_2.get(
            reverse('posts:profile_follow', args=['first_auth'])
        )
        Post.objects.create(
            author=self.author_2,
            text='Новый пост второго автора',
        )
        response = self.authorized_client_1.get(reverse('posts:follow_index'))
        first_post_on_page = response.context.get('page_obj')[0]
        self.assertEqual(first_post_on_page.text, 'Новый пост второго автора')

        response = self.authorized_client_2.get(reverse('posts:follow_index'))
        first_post_on_page = response.context.get('page_obj')[0]
        self.assertNotEqual(
            first_post_on_page.text, 'Новый пост второго автора'
        )
