from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from yatube.settings import POSTS_COUNT


CACHE_TIME = 20


def paginator(request, queryset):
    paginator = Paginator(queryset, POSTS_COUNT)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


#@cache_page(CACHE_TIME, key_prefix='index_page')
def index(request):
    posts = Post.objects.all().select_related('author', 'group')
    page_obj = paginator(request, posts)
    title = 'Последние обновления на сайте'
    context = {
        'title': title,
        'head_text': title,
        'page_obj': page_obj,
        'image_bg': 'img/home-bg.jpg',
    }
    template = 'posts/index.html'
    return render(request, template, context=context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    group_posts = group.group_posts.all().select_related('author')
    page_obj = paginator(request, group_posts)
    title = f'Записи сообщества  "{group.title}"'
    context = {
        'title': title,
        'head_text': title,
        'group': group,
        'page_obj': page_obj,
        'image_bg': 'img/group_posts.jpeg',
    }
    template = 'posts/group_list.html'
    return render(request, template, context=context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    author_posts = author.posts.all().select_related('group')
    page_obj = paginator(request, author_posts)
    following = request.user.is_authenticated and (
        request.user.follower.filter(author=author).exists()
    )
    title = f'Все посты пользователя {author.first_name} {author.last_name}'
    context = {
        'page_obj': page_obj,
        'author': author,
        'title': title,
        'head_text': title,
        'following': following,
        'image_bg': 'img/profile.png',
    }
    template = 'posts/profile.html'
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    comment_form = CommentForm(request.POST or None)
    comment_obj = post.comments.all()
    context = {
        'post': post,
        'head_text': 'Очередной интересный пост',
        'comment_form': comment_form,
        'comment_obj': comment_obj,
        'image_bg': 'img/post-bg.jpg',
    }
    template = 'posts/post_detail.html'
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    context = {
        'form': form,
        'title': 'Новый пост',
        'card_header': 'Новый пост',
        'submit_btn': 'Добавить',
    }
    template = 'posts/create_post.html'
    if request.method == "POST" and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user.username)
    return render(request, template, context=context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if not request.user == post.author:
        return redirect('posts:post_detail', post.pk)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    template = 'posts/create_post.html'
    context = {
        'form': form,
        'title': 'Редактировать пост',
        'card_header': 'Редактировать пост',
        'submit_btn': 'Сохранить',
        'post_id': post.pk,
        'is_edit': True,
    }
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect('posts:post_detail', post.pk)
    return render(request, template, context=context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    follower = Follow.objects.filter(user=request.user).values_list(
        "author_id", flat=True
    )
    fav_posts = Post.objects.filter(author_id__in=follower)
    page_obj = paginator(request, fav_posts)
    context = {
        'title': 'Избранные посты',
        'head_text': 'Избранное',
        'page_obj': page_obj,

    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.get(user=request.user, author=author).delete()
    return redirect('posts:follow_index')
