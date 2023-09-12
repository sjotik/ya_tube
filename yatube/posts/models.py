from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse

from yatube.settings import LEN_LIMIT


User = get_user_model()


class Post(models.Model):
    text = models.TextField(
        verbose_name='Текст',
        help_text='Поле для основного текстового содержания поста',
    )
    pub_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name='Дата публикации')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        'Group',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name='Сообщество',
        related_name='group_posts',
        help_text='Соотношение поста к тематической группе',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        verbose_name = "Публикация"
        verbose_name_plural = "Публикации"
        ordering = ('-pub_date',)

    def __str__(self):
        return self.text[:LEN_LIMIT]

    def get_absolute_url(self):
        return reverse("posts:post_detail", kwargs={"post_id": self.pk})


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name='Название сообщества'
    )
    slug = models.SlugField(unique=True, verbose_name='Адрес')
    description = models.TextField(verbose_name='Описание')

    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"
        ordering = ('id',)

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='К посту:',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор'
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Содержание комментария',
    )
    created = models.DateTimeField(auto_now_add=True,
                                   verbose_name='Дата создания')

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ('-created',)

    def __str__(self):
        return self.text[:LEN_LIMIT]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Подписан на',
        on_delete=models.CASCADE,
        related_name='following'
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        # на сколько я понялл подход по UniqueConstraint таков
        constraints = [
            models.UniqueConstraint(
                name='unique_couple',
                fields=['user', 'author'],
            )
        ]
