from http import HTTPStatus
import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings, TestCase
from django.urls import reverse

from ..models import Comment, Group, Post, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsCreateFormTests(TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        cache.clear()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        super().setUp()
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create_user(username='author')
        self.auth_client = Client()
        self.auth_client.force_login(self.user)
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        self.post = Post.objects.create(
            text='Тестовый текст',
            author=self.user,
        )

    def test_create_post_form_valid(self):
        """При отправке валидной формы создаётся новая запись"""
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
        data = {'text': 'Тестовый пост', 'image': uploaded}
        response = self.auth_client.post(
            reverse('posts:post_create'), data=data, follow=True)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={"username": self.user.username})
        )
        self.assertTrue(
            Post.objects.filter(
                text="Тестовый пост",
                image='posts/small.gif'
            ).exists())
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post_form_valid(self):
        """При отправке валидной формы редактируется запись"""
        posts_count = Post.objects.count()
        data = {'text': 'EDITED', 'group': self.group.pk}
        response = self.auth_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(Post.objects.get(pk=self.post.pk).text, 'EDITED')
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_guest_cant_edit_post(self):
        """Редактирование для гостя недоступно"""
        posts_count = Post.objects.count()
        data = {'text': 'EDITED', 'group': self.group.pk}
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(
            Post.objects.get(pk=self.post.pk).text,
            'Тестовый текст')
        self.assertRedirects(
            response,
            (reverse('users:login') + '?next='
             + reverse('posts:post_edit', kwargs={'post_id': self.post.pk}))
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_guest_cant_create_post(self):
        """Создание поста для гостя недоступно"""
        posts_count = Post.objects.count()
        data = {'text': 'Тестовый пост гостя'}
        response = self.guest_client.post(
            reverse('posts:post_create'), data=data, follow=True)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(
            Post.objects.filter(text="Тестовый пост гостя").exists())
        self.assertRedirects(
            response,
            (reverse('users:login') + '?next=' + reverse('posts:post_create'))
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)


class CommentCreateFormTests(TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.guest_client = Client()
        self.author = User.objects.create_user(username='author')
        self.user = User.objects.create_user(username='user')
        self.auth_client = Client()
        self.auth_client.force_login(self.user)
        self.post = Post.objects.create(
            text='Тестовый пост',
            author=self.author,
        )

    def test_create_comment_by_valid_form(self):
        """Валидная форма добавляет комментарий"""
        comment_count = Comment.objects.count()
        data = {
            'text': 'Тестовый комментарий',
            'author': self.user,
            'post': self.post,
        }
        response = self.auth_client.post(
            reverse('posts:add_comment', args=(self.post.pk,)),
            data=data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', args=(self.post.pk,))
        )
        self.assertTrue(
            Comment.objects.filter(text='Тестовый комментарий').exists())
        self.assertEqual(
            Comment.objects.get(text='Тестовый комментарий').post.pk,
            self.post.pk
        )

    def test_guest_cant_create_comment(self):
        """Добавление комментария для гостя недоступно"""
        comment_count = Comment.objects.count()
        comment_url = reverse('posts:add_comment', args=(self.post.pk,))
        data = {
            'text': 'Тестовый комментарий',
            'author': self.user,
            'post': self.post,
        }
        response = self.guest_client.post(
            comment_url,
            data=data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), comment_count)
        self.assertFalse(
            Comment.objects.filter(text='Тестовый комментарий').exists())
        self.assertRedirects(
            response,
            (reverse('users:login') + '?next=' + comment_url)
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
