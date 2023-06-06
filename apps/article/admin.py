from django.contrib import admin

from .models import Article, Tag, PostImage

class PostImageAdmin(admin.StackedInline):
    model = PostImage
    fields = ('post', 'images', 'cover_license_text')

class ArticleAdmin(admin.ModelAdmin):
    model = Article
    list_filter = ('category',)
    search_fields = ['title']
    list_display = ('title','category', 'created', 'is_pinned')
    filter_horizontal = ('tags',)
    fields = (
        'is_pinned',
        'cover',
        'cover_license_text',
        'title', 'category',
        'summary',
        'content',
        'is_content_markdown',
        'tags',
        'memo',
        'memo_text',
        'is_homepage',
        'created',
        'changed',
    )
    inlines = [PostImageAdmin]

class TagAdmin(admin.ModelAdmin):
    model = Tag
    list_display = ('name', 'sort')
    list_filter = ('name',)


admin.site.register(Article, ArticleAdmin)
admin.site.register(Tag, TagAdmin)


