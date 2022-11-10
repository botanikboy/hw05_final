from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from .utils import paginator_create


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.select_related('author', 'group')
    context = {
        'page_obj': paginator_create(post_list, request.GET.get('page')),
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    context = {
        'group': group,
        'page_obj': paginator_create(post_list, request.GET.get('page')),
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    user = request.user
    following = user.is_authenticated and Follow.objects.filter(
        user=user, author=author).exists()
    context = {
        'author': author,
        'page_obj': paginator_create(post_list, request.GET.get('page')),
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    user = request.user
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = user
        comment.post = post
        comment.save()
        return redirect('posts/post_detail.html', pk=post_id)
    else:
        context = {'form': form}
        comments = post.comments.all()
        context = {
            'post': post,
            'form': form,
            'comments': comments,
        }
        return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    user = request.user
    if form.is_valid():
        post = form.save(commit=False)
        post.author = user
        post.save()
        return redirect('posts:profile', user.username)
    else:
        context = {'form': form}
        return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if post.author != request.user:
        return redirect('posts:post_detail', post.id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post.id)

    context = {
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


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
    user = request.user
    post_list = Post.objects.filter(author__following__user__id=user.id)
    context = {
        'page_obj': paginator_create(post_list, request.GET.get('page')),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if (
        user != author
        and not
        Follow.objects.filter(user=user, author=author).exists()
    ):
        Follow.objects.create(user=user, author=author)
    return redirect('posts:profile', author.username)


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if Follow.objects.filter(user=user, author=author).exists():
        Follow.objects.get(user=user, author=author).delete()
    return redirect('posts:profile', author.username)
