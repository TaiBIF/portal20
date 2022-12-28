from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404
from django.views import generic
from django.core.paginator import Paginator

from .models import Article, PostImage
from itertools import chain

CODE_MAPPING ={
    'cat':{
        'news':'新聞', 
        'event':'活動',
        'update':'更新',
        'sci':'科普文章',
        'tech':'技術專欄',
        'pub':'出版品資料',
        'pos':'TaiBIF發表文章/海報',
    }
}
#DEPRICATED 不合用
class ArticleListView(generic.ListView):
    template_name = 'article-list.html'
    #context_object_name = 'article_list'

    #def get_queryset(self):
    #    return Article.objects
    model = Article
    paginate_by = 10  # if pagination is desired
    def get_context_data(self, *args ,**kwargs):
        print (kwargs, args)
        context = super().get_context_data(**kwargs)
        return context

#DEPRICATED 不好用
class ArticleDetailView(generic.DetailView):
    model = Article
    template_name = 'article-detail.html'

def article_list(request, category):
    page = request.GET.get('page', '')
    valid_category = [x for x in Article.CATEGORY_CHOICE \
                      if x[0].lower() == category]

    if not valid_category:
        raise Http404('category does not exist')
    query = Article.objects.filter(
        category=category.upper(),
        is_pinned='N'
    ).all()
    cover_list = Article.objects.filter(
        category=category.upper(),
        is_pinned='Y'
    )

    rows = []
    if request.GET.get('start', '') and request.GET.get('end', ''):
        query = query.filter(created__range=[request.GET['start'], request.GET['end']])

    rows = query.all()
    paginator = Paginator(rows, 20)
    article_list = paginator.get_page(page)

    layout_type = ''
    if category in ['news', 'event', 'update']:
        layout_type = 'A1'
    elif category in ['sci', 'tech', 'pub', 'pos']:
        layout_type = 'A2'

    return render(request, 'article-list.html', {
        'article_list': article_list,
        'cover_list': cover_list,
        'article_cat': category,
        'article_cat_ch': CODE_MAPPING['cat'][category],
        'article_cat_label': valid_category[0][1],
        'layout_type': layout_type,
    })


def article_detail(request, pk):
    article = get_object_or_404(Article, pk=pk)
    imagesList = PostImage.objects.filter(post=pk)
    recommended = Article.objects.filter(category=article.category).order_by('?')[0:5]
    return render(request, 'article-detail.html', {
        'article': article,
        'article_type': dict(article.CATEGORY_CHOICE)[article.category],
        'recommended': recommended,
        'imagesList': imagesList
    })


def article_search(request):
    page = request.GET.get('page', '')
    article_cat = []
    article_search_keyword =''
    for key, values in request.GET.lists():
        if key == "q":
            article_search_keyword = values[0]
        if key == "category":
            for i in values:
                article_cat.append(i.upper())

    if article_cat :
        if article_search_keyword:
            rows = Article.objects.filter(category__in=article_cat,title__icontains=article_search_keyword).all()
            cover_list = Article.objects.filter(category__in=article_cat,title__icontains=article_search_keyword,is_pinned='Y')
        else:
            rows = Article.objects.filter(category__in=article_cat).all() 
            cover_list = Article.objects.filter(category__in=article_cat,is_pinned='Y')
    else:
        rows = Article.objects.filter(title__icontains=article_search_keyword).all()    
        cover_list = Article.objects.filter(title__icontains=article_search_keyword,is_pinned='Y')
    
    paginator = Paginator(rows, 20)
    article_list = paginator.get_page(page)
    
    return render(request, 'article-list.html', {
        'article_list': article_list,
        'cover_list': cover_list,
        'article_cat': article_cat,
        'article_search_keyword': article_search_keyword,
    })
def article_tag_list(request, tag_name):
    page = request.GET.get('page', '')
    rows = Article.objects.filter(tags__name=tag_name).all()
    paginator = Paginator(rows, 20)
    article_list = paginator.get_page(page)


    return render(request, 'article-tag-list.html', {
        'article_list': article_list,
    })
