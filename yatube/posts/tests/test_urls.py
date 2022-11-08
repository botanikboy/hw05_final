from http import HTTPStatus

from django.test import TestCase, Client
from django.core.cache import cache

from posts.models import Post, Group, User


class StaticURLTests(TestCase):
    def test_homepage(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_1,
            text='Тестовый пост на много символов, '
            'чтобы проверить длину вывода метода str().',
            group=cls.group,
        )

    def setUp(self):
        self.user_2 = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_2)
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user_1)
        cache.clear()

    def test_public_urls_exists_at_desired_location(self):
        urls = {
            '/': HTTPStatus.OK,
            '/group/test-slug/': HTTPStatus.OK,
            '/profile/HasNoName/': HTTPStatus.OK,
            '/posts/1/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for address, status_code in urls.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, status_code)

    def test_post_create_url_exists_at_desired_location_authorized(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_exists_at_desired_location_authorized(self):
        response = self.authorized_client.get('/posts/1/edit/')
        self.assertRedirects(
            response, ('/posts/1/'))

    def test_post_edit_url_exists_at_desired_location_authorized_author(self):
        response = self.authorized_client_author.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_url_redirect_anonymous(self):
        response = self.client.get('/create/')
        self.assertRedirects(
            response, ('/auth/login/?next=/create/'))

    def test_post_edit_url_redirect_anonymous(self):
        response = self.client.get('/posts/1/edit/')
        self.assertRedirects(
            response, ('/auth/login/?next=/posts/1/edit/'))

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/HasNoName/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            '/posts/1/edit/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client_author.get(address)
                self.assertTemplateUsed(response, template)
