from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовый пост',
        )

    def setUp(self):
        super().setUp()
        cache.clear()
        self.guest_client = Client()
        self.user_not_author = User.objects.create_user(username='user')
        self.not_author_client = Client()
        self.not_author_client.force_login(self.user_not_author)
        self.author_client = Client()
        self.author_client.force_login(PostsURLTests.user_author)
        self.users = [
            self.author_client,
            self.not_author_client,
            self.guest_client
        ]
        self.index_url = reverse('posts:index')
        self.group_list_url = reverse(
            'posts:group_list', args=(PostsURLTests.group.slug,))
        self.profile_url = reverse(
            'posts:profile', args=(PostsURLTests.post.author,))
        self.post_detail_url = reverse(
            'posts:post_detail', args=(PostsURLTests.post.pk,))
        self.post_edit_url = reverse(
            'posts:post_edit', args=(PostsURLTests.post.pk,))
        self.post_create_url = reverse('posts:post_create')
        self.unexisting_page = '/unexisting_page/'
        self.urls_templates_for_guest = {
            self.index_url: 'posts/index.html',
            self.group_list_url: 'posts/group_list.html',
            self.profile_url: 'posts/profile.html',
            self.post_detail_url: 'posts/post_detail.html',
        }
        self.urls_templates_for_auth = {
            self.post_edit_url: 'posts/create_post.html',
            self.post_create_url: 'posts/create_post.html',
        }

    def test_url_exists_at_desired_location(self):
        """Проверка доступности страниц пользователям"""
        for address in self.urls_templates_for_guest.keys():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f'Ошибка доступности общей страницы "{address}"'
                )
        for address in self.urls_templates_for_auth.keys():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f'Ошибка доступности страницы "{address}" '
                    f'для авторизованного пользователя'
                )

    def test_url_create_redirect_anonymous_on_login(self):
        """Страница создания поста перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get(self.post_create_url, follow=True)
        self.assertRedirects(
            response,
            (reverse('users:login') + '?next=' + self.post_create_url)
        )

    def test_url_editpage_redirect_guest_on_login(self):
        """Страница редактирования поста перенаправит гостя
        на страницу логина.
        """
        response_gst = self.guest_client.get(self.post_edit_url, follow=True)
        self.assertRedirects(
            response_gst,
            (reverse('users:login') + '?next=' + self.post_edit_url)
        )

    def test_url_editpage_redirect_not_author_on_detail(self):
        """Страница редактирования поста перенаправит не автора на
        страницу просмотра поста.
        """
        response_not_author = self.not_author_client.get(
            self.post_edit_url,
            follow=True
        )
        self.assertRedirects(
            response_not_author,
            self.post_detail_url,
        )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        merged_urls = {
            **self.urls_templates_for_guest,
            **self.urls_templates_for_auth,
            '/unexisting_page/': 'core/404.html',
        }
        for address, template in merged_urls.items():
            response = self.author_client.get(address)
            self.assertTemplateUsed(
                response,
                template,
                f'Проблема соответствия шаблона со страницей "{address}"'
            )

    def test_request_unexisting_page_return_404(self):
        """Несуществующая страница вернет 404 для всех"""
        for user in self.users:
            with self.subTest(user=user):
                response = user.get(self.unexisting_page)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
