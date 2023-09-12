"""from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client


User = get_user_model()


class UsersURLTests(TestCase):
    def setUp(self):
        super().setUp()
        self.guest_client = Client()
        self.user = User.objects.create(username='user', password='P@ssw0rd')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.users = [
            self.authorized_client,
            self.guest_client
        ]
        self.urls_templates = {
            '/auth/signup/': 'users/signup.html',
            '/auth/login/': 'users/login.html',
            '/auth/logout/': 'users/logged_out.html',
            '/auth/password_reset/': 'users/password_reset_form.html',
            '/auth/password_reset/done/': 'users/password_reset_done.html',
            '/auth/reset/done/': 'users/password_reset_complete.html',
            '/auth/password_change/': 'users/password_change_form.html',
            '/auth/password_change_done/': 'users/password_change_done.html',
        }

    def test_01(self):
        response1 = self.authorized_client.get('/auth/password_change/')
        response2 = self.guest_client.get('/auth/password_change/')
        self.assertEqual(response1.status_code, HTTPStatus.OK)
        self.assertEqual(response2.status_code, HTTPStatus.FOUND)



    def test_02(self):
        urls = [x for x in self.urls_templates.keys()]
        response1 = self.authorized_client.get(urls[6])
        self.assertEqual(response1.status_code, HTTPStatus.OK)

        for address in urls:
            with self.subTest(address=address):
                response5 = self.authorized_client.get(address)
                self.assertEqual(response5.status_code, HTTPStatus.OK)
"""
