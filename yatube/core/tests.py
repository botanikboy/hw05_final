from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse

from posts.models import User


class CoreURLTests(TestCase):
    def test_404_uses_correct_template(self):
        page_404 = '/unexisting_page/'
        self.assertEqual(
            self.client.get(page_404).status_code,
            HTTPStatus.NOT_FOUND
        )
        self.assertTemplateUsed(self.client.get(page_404), 'core/404.html')

    def test_csrf_token_check_page_uses_correct_template(self):
        User.objects.create_user(username='auth')
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(User.objects.get(username='auth'))
        form_data = {
            'text': 'Тестовый текст нового поста',
            'group': 1,
        }
        response = csrf_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertTemplateUsed(response, 'core/403csrf.html')
