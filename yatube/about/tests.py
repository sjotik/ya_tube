from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse


class AboutURLTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.guest_client = Client()
        self.urls_templates = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
        }

    def test_url_exists_at_desired_location(self):
        """Проверка доступности страниц пользователям"""
        for address in self.urls_templates.keys():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f'Проблема со страницей "{address}"'
                )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, template in self.urls_templates.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(
                    response,
                    template,
                    f'Проблема соответствия шаблона со страницей "{address}"'
                )
