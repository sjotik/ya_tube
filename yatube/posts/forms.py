from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image',)
        help_texts = {
            'text': 'Поле для основного текстового содержания поста',
            'group': 'Соотношение поста к тематической группе',
            'image': 'Добавить изображение',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        help_texts = {
            'text': 'Содержание комментария',
        }
