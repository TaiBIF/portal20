from django.contrib import admin

from .models import Article, Tag

class ArticleAdmin(admin.ModelAdmin):
    model = Article
    list_filter = ('category',)
    list_display = ('title','category', 'created', 'is_pinned')
    filter_horizontal = ('tags',)
    fields = ('is_pinned', 'cover', 'cover_license_text', 'title', 'category', 'content', 'tags', 'memo', 'memo_text')

class TagAdmin(admin.ModelAdmin):
    model = Tag
    list_display = ('name', 'sort')
    list_filter = ('name',)


admin.site.register(Article, ArticleAdmin)
admin.site.register(Tag, TagAdmin)
