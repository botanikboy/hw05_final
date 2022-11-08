from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus

User = get_user_model()


class PostsURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_public_urls_exists_at_desired_location(self):
        urls = {
            '/auth/logout/': HTTPStatus.OK,
            '/auth/signup/': HTTPStatus.OK,
            '/auth/login/': HTTPStatus.OK,
            '/auth/password_change/': HTTPStatus.FOUND,
            '/auth/password_change/done/': HTTPStatus.FOUND,
            '/auth/password_reset/': HTTPStatus.OK,
            '/auth/password_reset/done/': HTTPStatus.OK,
            '/auth/reset/<uidb64>/<token>/': HTTPStatus.OK,
            '/auth/reset/done/': HTTPStatus.OK,
        }
        for address, status_code in urls.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status_code)

    def test_password_change_url_exists_at_desired_location_authorized(self):
        response = self.authorized_client.get('/auth/password_change/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_password_change_done_url_exists_at_desired_location_authorized(
        self
    ):
        response = self.authorized_client.get('/auth/password_change/done/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_password_change_url_redirect_anonymous(self):
        response = self.guest_client.get('/auth/password_change/')
        self.assertRedirects(
            response, ('/auth/login/?next=/auth/password_change/'))

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            '/auth/logout/': 'users/logged_out.html',
            '/auth/signup/': 'users/signup.html',
            '/auth/login/': 'users/login.html',
            '/auth/password_reset/': 'users/password_reset_form.html',
            '/auth/password_reset/done/': 'users/password_reset_done.html',
            '/auth/reset/<uidb64>/<token>/':
                'users/password_reset_confirm.html',
            '/auth/reset/done/': 'users/password_reset_complete.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
