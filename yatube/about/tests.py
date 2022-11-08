from django.test import TestCase
from http import HTTPStatus


class PublicURLTests(TestCase):
    def test_public_urls_exists_at_desired_location(self):
        urls = {
            '/about/author/': HTTPStatus.OK,
            '/about/tech/': HTTPStatus.OK,
        }
        for address, status_code in urls.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, status_code)

    def test_public_urls_uses_correct_template(self):
        templates_url_names = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertTemplateUsed(response, template)
