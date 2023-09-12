import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings, TestCase
from django.urls import reverse

from posts.models import Follow, Group, Post, User


POSTS_COUNT = 15
PAG_LIMIT = 10
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
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
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        super().setUp()
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.f_user = User.objects.create(username='f_user')
        self.follow_client = Client()
        self.follow_client.force_login(self.f_user)
        self.uf_user = User.objects.create(username='uf_user')
        self.unfollow_client = Client()
        self.unfollow_client.force_login(self.uf_user)
        self.username = PostsPagesTests.user.username
        self.post_pk = PostsPagesTests.post.pk
        self.slug = PostsPagesTests.group.slug

    def assertion_first_obj_context(self, response, exp_title=None):
        """Метод проверки контекста 1го объекта на странице"""
        first_obj = response.context['page_obj'][0]
        self.assertEqual(first_obj.text, 'Тестовый пост')
        self.assertEqual(first_obj.group.title, 'Тестовая группа')
        self.assertEqual(first_obj.author.username, 'author')
        if exp_title is not None:
            cur_title = response.context.get('title')
            self.assertEqual(cur_title, exp_title)

    def assertion_form_fields(self, response):
        """Метод проверки полей формы"""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            (reverse(
                'posts:group_list', kwargs={'slug': self.slug}
            )): 'posts/group_list.html',
            (reverse(
                'posts:profile', kwargs={'username': self.username}
            )): 'posts/profile.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            (reverse(
                'posts:post_edit', kwargs={'post_id': self.post_pk}
            )): 'posts/create_post.html',
            (reverse(
                'posts:post_detail', kwargs={'post_id': self.post_pk}
            )): 'posts/post_detail.html',
        }
        for name, template in templates_pages_names.items():
            with self.subTest(name=name):
                response = self.authorized_client.get(name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон INDEX сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIn('title', response.context, 'Не передан "title"')
        self.assertIn(
            'page_obj', response.context, 'Не передан объект страницы'
        )
        exp_title = 'Последние обновления на сайте'
        self.assertion_first_obj_context(response)
        self.assertion_first_obj_context(response, exp_title)

    def test_group_list_page_show_correct_context(self):
        """Шаблон GROUP_LIST сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': PostsPagesTests.group.slug})
        )
        self.assertIn('title', response.context, 'Не передан "title"')
        self.assertIn(
            'page_obj', response.context, 'Не передан объект страницы'
        )
        self.assertIn('group', response.context, 'Не передан "group"')
        group = response.context.get('group').title
        exp_title = f'Записи сообщества {group}'
        self.assertion_first_obj_context(response, exp_title)

    def test_profile_page_show_correct_context(self):
        """Шаблон PROFILE сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': PostsPagesTests.user.username})
        )
        self.assertIn('author', response.context, 'Не передан "author"')
        self.assertIn(
            'page_obj', response.context, 'Не передан объект страницы'
        )
        self.assertion_first_obj_context(response)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон POST_DETAIL сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': PostsPagesTests.post.pk}))
        self.assertIn('post', response.context, 'Не передан "post"')
        post_id = response.context.get('post').id
        post_text = response.context.get('post').text
        post_group = response.context.get('post').group.title
        post_author = response.context.get('post').author.username
        self.assertEqual(post_id, PostsPagesTests.post.pk)
        self.assertEqual(post_text, 'Тестовый пост')
        self.assertEqual(post_group, 'Тестовая группа')
        self.assertEqual(post_author, 'author')

    def test_post_create_page_show_correct_context(self):
        """Шаблон POST_CREATE сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        context_items = ('title', 'form', 'card_header', 'submit_btn')
        context_items = {
            'title': 'Новый пост',
            'card_header': 'Новый пост',
            'submit_btn': 'Добавить',
        }
        for item, value in context_items.items():
            with self.subTest(item=item):
                self.assertIn(
                    item, response.context, f'В шаблон не был передан {item}'
                )
                self.assertEqual(
                    response.context.get(item),
                    value,
                    f'Неверное содержимое {item} в контексте'
                )
        self.assertion_form_fields(response)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон POST_EDIT сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostsPagesTests.post.pk}))
        context_items = {
            'title': 'Редактировать пост',
            'card_header': 'Редактировать пост',
            'submit_btn': 'Сохранить',
            'post_id': PostsPagesTests.post.pk,
            'is_edit': '',
        }
        for item, value in context_items.items():
            with self.subTest(item=item):
                self.assertIn(
                    item, response.context, f'В шаблон не был передан {item}'
                )
                if item != 'is_edit':
                    self.assertEqual(
                        response.context.get(item),
                        value,
                        f'Неверное содержимое {item} в контексте')
                else:
                    self.assertTrue(item)

        self.assertion_form_fields(response)

    def test_show_group_post_on_pages(self):
        """Пост с группой отображается на index, group_list и profile"""
        names = (
            reverse('posts:index'),
            (reverse('posts:group_list',
                     kwargs={'slug': PostsPagesTests.group.slug})),
            (reverse(
                'posts:profile',
                kwargs={'username': PostsPagesTests.post.author})),
        )
        expected = Post.objects.get(group=PostsPagesTests.group)
        for name in names:
            with self.subTest(name=name):
                response = self.authorized_client.get(name).context['page_obj']
                self.assertIn(
                    expected,
                    response,
                    f'Проблема отображения поста с группой на "{name}"'
                )

    def test_wrong_show_group_post_on_other_group_pages(self):
        """Пост с группой не отображается в других группах"""
        address = (reverse('posts:group_list',
                           kwargs={'slug': PostsPagesTests.group.slug}))
        response = self.authorized_client.get(address).context['page_obj']
        expected = Post.objects.exclude(group=PostsPagesTests.group)
        self.assertNotIn(
            expected,
            response,
            'Пост отображается в ошибочной группе'
        )

    def test_pages_gets_image(self):
        """Изображение передается на страницы INDEX, GROUP_LIST, PROFILE"""
        page_urls = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.slug}),
            reverse(
                'posts:profile', kwargs={'username': self.username}),
        )
        for url in page_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                result = response.context['page_obj'][0]
                self.assertEqual(result.image, self.post.image)

    def test_page_detail_gets_image(self):
        """Изображение передается на страницу DETAIL"""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post_pk})
        )
        result = response.context['post']
        self.assertEqual(result.image, self.post.image)

    def test_post_with_img_exists(self):
        """Пост с изображением есть в базе"""
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый пост',
                image='posts/small.gif'
            ).exists()
        )

    def test_cache_index_page(self):
        """Проверка кэширования страницы INDEX"""
        response1 = self.authorized_client.get(reverse('posts:index'))
        content_before = response1.content
        Post.objects.get(pk=1).delete()
        response2 = self.authorized_client.get(reverse('posts:index'))
        content_after = response2.content
        self.assertEqual(content_before, content_after)

    def test_follow_unfollow_auth_user(self):
        """Проверка подписки/отписки на автора"""
        def response():
            return self.follow_client.get(reverse('posts:follow_index'))

        def assertion_follow_result(queryset, exp: int, follow=True):
            if follow:
                self.assertEqual(
                    len(queryset.context['page_obj']),
                    exp,
                    'Не работает подписка')
            else:
                self.assertEqual(
                    len(queryset.context['page_obj']),
                    exp,
                    'Не работает отписка')

        before_rsp = response()
        assertion_follow_result(before_rsp, 0)
        Follow.objects.get_or_create(user=self.f_user, author=self.post.author)
        after_rsp = response()
        assertion_follow_result(after_rsp, 1)
        self.assertIn(
            self.post,
            after_rsp.context["page_obj"],
            'Пост автора не появился в ленте подписчика')
        uf_client_rsp = self.unfollow_client.get(reverse('posts:follow_index'))
        self.assertNotIn(
            self.post,
            uf_client_rsp.context["page_obj"],
            'Пост автора в ленте НЕподписчика'
        )
        Follow.objects.filter(
            user=self.f_user, author=self.post.author).delete()
        unfollow_rsp = response()
        assertion_follow_result(unfollow_rsp, 0, follow=False)


class PaginatorViewsTest(TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.user = User.objects.create_user(username='author')
        self.auth_client = Client()
        self.auth_client.force_login(self.user)
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        for i in range(POSTS_COUNT):
            self.post = Post.objects.create(
                author=self.user,
                text=f'Тестовый пост {i}',
                group=self.group
            )

    def test_first_page_contains_pag_limit_posts(self):
        """Страница содержит, ограниченное паджинатором, количество записей"""
        response = self.auth_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), PAG_LIMIT)

    def test_second_page_contains_other_posts(self):
        """Страница содержит, на последней странице паджинатора,
        оставшееся количество записей"""
        response = self.auth_client.get(reverse('posts:index') + '?page=2')
        diff_count = len(Post.objects.all()) - PAG_LIMIT
        self.assertEqual(len(response.context['page_obj']), diff_count)
