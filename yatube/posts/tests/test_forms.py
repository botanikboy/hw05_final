import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from posts.models import Post, Group, User, Comment


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст нового поста',
            'group': 1,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': 'auth'})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст нового поста',
                group_id=1,
                image='posts/small.gif',
            ).exists()
        )

    def test_edit_post(self):
        form_data = {
            'text': 'Редактированный тестовый текст нового поста',
            'group': '',
        }
        self.client.post(
            reverse('posts:post_edit', kwargs={'post_id': 1}),
            data=form_data,
            follow=True
        )
        self.assertEqual(
            self.post.text,
            'Тестовый пост на много символов, '
            'чтобы проверить длину вывода метода str().'
        )

        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': 1}),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            self.post.text,
            'Редактированный тестовый текст нового поста'
        )
        self.assertIsNone(Post.objects.get(pk=1).group)

    def test_cant_create_empty_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': '',
            'group': 2,
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
        self.assertEqual(response.status_code, 200)


class CommentFormTests(TestCase):
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
            text='Тестовый текст поста',
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_comment(self):
        comments_count = self.post.comments.count()
        form_data = {'text': 'Тестовый текст комментария'}
        self.client.post(
            reverse('posts:add_comment', kwargs={'post_id': 1}),
            data=form_data,
        )
        self.assertEqual(self.post.comments.count(), comments_count)

        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': 1}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': 1})
        )
        self.assertEqual(self.post.comments.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(text='Тестовый текст комментария').exists()
        )

        response = self.client.get(
            reverse('posts:post_detail', kwargs={'post_id': 1})
        )
        last_comment_on_page = response.context.get('comments')[0]
        comment_text = last_comment_on_page.text
        self.assertEqual(comment_text, 'Тестовый текст комментария')
