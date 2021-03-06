from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from django.core.mail import send_mail
from django.db.models import Count
from .forms import EmailPostForm, CommentForm, SearchForm
from .models import Post
from taggit.models import Tag
from haystack.query import SearchQuerySet


class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'MyBlg/post/list.html'


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post, slug=post,
                             status='published',
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)
    #Lista aktywnych komentarzy dla danego posta:
    comments = post.comments.filter(active=True)

    if request.method == 'POST':
        #komentarz został opublikowany
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.post = post
            new_comment.save()
    else:
        comment_form = CommentForm()

    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]
    return render(request,
                  'MyBlg/post/detail.html', {'post': post,
                                             'comments': comments,
                                             'comment_form': comment_form,
                                             'similar_posts': similar_posts})


def post_list(request, tag_slug=None):
    object_list = Post.published.all()
    tag = None

    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        object_list = object_list.filter(tags__in=[tag])

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
                   'posts': posts,
                   'tag': tag})


def post_share(request, post_id):
    # Pobierz post na podstawie jego id
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False

    if request.method == 'POST':
        # Formularz został wysłany
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # weryfikacja zakończyła się sukcesem
            cd = form.cleaned_data
            # zatem wyślij maila
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = '{} ({}) zachęca do przeczytania "{}"'.format(cd['name'], cd['email'], post.title)
            message = 'Przeczytaj post "{}" na stronie {}\n\nKomentarz dodany przez {}: {}'.format(post.title,
                                                                                                   post_url,
                                                                                                   cd['name'],
                                                                                                   cd['comments'])
            send_mail(subject, message, 'admin@myblog.com', [cd['to']])
            sent = True
    else:
        form = EmailPostForm()
    return render(request,
                  'MyBlg/post/share.html', {'post': post,
                                            'form': form,
                                            'sent': sent})


def post_search(request):
    form = SearchForm()
    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            cd = form.cleaned_data
            results = SearchQuerySet().models(Post).filter(content=cd['query']).load_all()
            # Obliczenie całkowitej liczby wyników
            total_results = results.count()
            return render(request, 'MyBlg/post/search.html', {'form': form,
                                                              'cd': cd,
                                                              'results': results,
                                                              'total_results': total_results})
    else:
        return render(request, 'MyBlg/post/search.html', {'form': form})
