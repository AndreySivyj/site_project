from django.shortcuts import render, get_object_or_404
from django.http import Http404
from .models import Post, Comment
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from .forms import EmailPostForm, CommentForm
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from taggit.models import Tag
from django.db.models import Count


def post_list(request, tag_slug=None):
    post_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_list = post_list.filter(tags__in=[tag])

    #Постраничная разбивка с 3 постами на страницу
    paginator = Paginator(post_list, 3)
    page_number = request.GET.get('page', 1)
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        # Если page_number не целое число, то выдем первую страницу
        posts = paginator.page(1)
    except EmptyPage:
        # Если page_number находится вне диапазона, то выдем последнюю страницу
        posts = paginator.page(paginator.num_pages)
    return render(request, 'blog/post/list.html', {'posts': posts, 'tag': tag})


def post_detail(request, year, month, day, post):    
    # try:
        # post = Post.published.get(id=id)
    # except Post.DoesNotExist:
    #     raise Http404("No Post found.")

    # post = get_object_or_404(Post, id=id, status=Post.Status.PUBLISHED)

    post = get_object_or_404(Post, 
                             status=Post.Status.PUBLISHED,
                             slug=post,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day,
                             )
    
    # Список активных комментариев к этому посту
    comments = post.comments.filter(active=True) # используем related_name='comments' модели Comment, соответственно можем обратиться post.comments
    # Форма для комментирования пользователями
    form = CommentForm()

    # Список схожих постов
    post_tags_ids = post.tags.values_list('id', flat=True) # values_list() возвращает кортежи со значениями заданных полей
    # flat=True, чтобы получить одиночные значения, такие как [1, 2, 3, ...], а не одноэлементые кортежи, такие как [(1,), (2,), (3,) ...]
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id) # берем все посты, содержащие любой из этих тегов, за исключением текущего поста
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags','-publish')[:4]
    # функция агрегирования Count генерирует вычисляемое поле – same_tags, которое содержит число тегов, общих со всеми запрошенными тегами
    # результат упорядочивается по числу общих тегов (в убывающем порядке) и по publish, нарезается, чтобы получить только первые четыре поста

    return render(request, 'blog/post/detail.html', {
                                                    'post': post, 
                                                    'comments': comments, 
                                                    'form': form, 
                                                    'similar_posts': similar_posts
                                                    })


class PostListView(ListView):
    """
    Альтернативное представление списка постов
    """
    queryset = Post.published.all() # можно указать model=Post и Django сформирует типовой набор запросов Post.objects.all()
    context_object_name = 'posts' # если не указано имя контекстного объекта context_object_name, то по умолчанию используется переменная object_list
    paginate_by = 3
    template_name = 'blog/post/list.html' # если шаблон не задан, то по умолчанию List-View будет использовать blog/post_list.html


def post_share(request, post_id):
    # Извлечь пост по идентификатору id
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)

    sent = False

    if request.method == 'POST':
        # Форма была передана на обработку
        form = EmailPostForm(request.POST)
        if form.is_valid():                 # Список ошибок валидации можно получить посредством form.errors
            # Поля формы успешно прошли валидацию
            cd = form.cleaned_data
            # ... отправить электронное письмо
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read {post.title}"
            message = f"Read {post.title} at {post_url}\n\n {cd['name']}\'s comments: {cd['comments']}"
            send_mail(subject, message, 'your_account@gmail.com', [cd['to']])
            sent = True
    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html', {'post': post, 'form': form, 'sent':sent})


@require_POST # ограничиваем разрешенные для представления HTTP-методы -> если обращаться не POST-методом, то будет ошибка HTTP 405 (Метод не разрешен)
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    comment = None
    # Комментарий был отправлен
    form = CommentForm(data=request.POST)
    if form.is_valid():
        # Создать объект класса Comment, не сохраняя его в базе данных
        comment = form.save(commit=False) # commit=False позволяет видоизменять объект перед его окончательным сохранением в БД
        # Назначить пост комментарию
        comment.post = post        
        # Сохранить комментарий в базе данных
        comment.save()
    return render(request, 'blog/post/comment.html', {'post': post, 'form': form, 'comment': comment})
