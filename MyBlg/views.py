from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Post


def post_list(request):
    posts = Post.published.all()
    return render(request,
                  'MyBlg/post/list.html', {'posts': posts})


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post, slug=post,
                             status='published',
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)
    return render(request,
                  'MyBlg/post/detail.html', {'post': post})


def post_list(request):
    object_list = Post.published.all()
    paginator = Paginator(object_list, 3)   # Trzy posty na stronę
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        # Jeżeli liczba stron nie jest liczbą całkowitą, zwróć pierwszą stronę
        posts = paginator.page(1)
    except EmptyPage:
        # Jeżeli zmienna page ma wartość większą niż liczba stron, to wtedy pobierana jest ostatnia strona
        posts =paginator.page(paginator.num_pages)
    return render(request,
                  'MyBlg/post/list.html',
                  {'page': page,
                   'posts': posts})


