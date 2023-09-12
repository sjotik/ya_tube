from django.test import TestCase

from ..models import Group, Post, User
from yatube.settings import LEN_LIMIT


TEST_TEXT_LEN = 10


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост' * TEST_TEXT_LEN,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        group = PostModelTest.group
        models_strings = {
            post: post.text[:LEN_LIMIT],
            group: group.title,
        }
        for model, string in models_strings.items():
            with self.subTest(model=model):
                self.assertEqual(
                    str(model),
                    string,
                    'Проблема с __str__ модели'
                )

    def test_title_field_label(self):
        """Проверка корректности отображения verbose_name моделей"""
        post = PostModelTest.post
        group = PostModelTest.group
        verb_post = post._meta.get_field('text').verbose_name
        verb_group = group._meta.get_field('title').verbose_name
        verbnames_exptext = {
            verb_post: 'Текст',
            verb_group: 'Название сообщества',
        }
        for verbname, exptext in verbnames_exptext.items():
            with self.subTest(verbname=verbname):
                self.assertEqual(
                    verbname,
                    exptext,
                    'Проблема с verbose_name',
                )

    def test_field_help_text(self):
        """Проверка корректности отображения help_text моделей"""
        post = PostModelTest.post
        ht_post = post._meta.get_field('text').help_text
        self.assertEqual(
            ht_post,
            'Поле для основного текстового содержания поста',
            'Проблема с help_text модели Post'
        )
