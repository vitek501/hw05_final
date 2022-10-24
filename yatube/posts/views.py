from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.cache import cache_page
from .utils import get_page_context
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm


@cache_page(20, key_prefix='index_page')
def index(request):
    posts = Post.objects.all()
    page_obj = get_page_context(posts, request)
    context = {
        'page_obj': page_obj,
        'title': 'Последние обновления на сайте'
    }
    template = 'posts/index.html'
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.grouped_posts.all()
    page_obj = get_page_context(posts, request)
    context = {
        'group': group,
        'page_obj': page_obj,
        'title': f'Записи сообщества {group}'
    }
    template = 'posts/group_list.html'
    return render(request, template, context)


def profile(request, username):
    username = get_object_or_404(User, username=username)
    posts_user = Post.objects.filter(author=username)
    page_obj = get_page_context(posts_user, request)
    following = False
    if request.user.is_authenticated:
        following = request.user.follower.filter(author=username).exists()
    context = {
        'title': f'{username.get_full_name()} профайл пользователя',
        'author': username,
        'page_obj': page_obj,
        'following': following,
    }
    template = 'posts/profile.html'
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    posts_count = Post.objects.filter(author=post.author).count()
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    context = {
        'title': 'Пост ' + post.text[:30],
        'post': post,
        'posts_count': posts_count,
        'form': form,
        'comments': comments
    }
    template = 'posts/post_detail.html'
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        user = request.user.username
        post.author = request.user
        post.save()
        return redirect('posts:profile', user)
    context = {'form': form,
               'title': 'Новый пост',
               }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {'title': 'Редактировать пост',
               'post': post,
               'form': form,
               'is_edit': True,
               }
    template = 'posts/create_post.html'
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.select_related(
        'author', 'group').filter(
            author__following__user=request.user
    ).prefetch_related('comments')
    page_obj = get_page_context(posts, request)
    context = {'page_obj': page_obj}
    template = 'posts/follow.html'
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    follower = request.user
    author = get_object_or_404(User, username=username)
    if follower != author:
        Follow.objects.get_or_create(user=follower, author=author)
    previous_path = request.META.get('HTTP_REFERER')
    return redirect(previous_path if previous_path else 'posts:profile',
                    username)


@login_required
def profile_unfollow(request, username):
    follower = request.user
    author = get_object_or_404(User, username=username)
    follower.follower.filter(author=author).delete()
    previous_path = request.META.get('HTTP_REFERER')
    return redirect(previous_path if previous_path else 'posts:profile',
                    username)
