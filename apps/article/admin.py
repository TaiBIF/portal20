from django.contrib import admin
from django import forms
from django.utils.html import format_html

from .models import Article, Tag, PostImage, CaseType, CaseMedia, ArticleImageAsset

class PostImageAdmin(admin.StackedInline):
    model = PostImage
    fields = ('post', 'images', 'cover_license_text')

class CaseMediaAdmin(admin.StackedInline):
    model = CaseMedia
    fields = ('post', 'media_name', 'media_url')

class ArticleAdminForm(forms.ModelForm):
    category = forms.MultipleChoiceField(
        label='分類',
        choices=Article.CATEGORY_CHOICE,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Article
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.initial['category'] = self.instance.category_list
        else:
            self.initial['category'] = [Article._meta.get_field('category').default]

    def clean_category(self):
        return Article.normalize_category_value(self.cleaned_data['category'])

class ArticleCategoryListFilter(admin.SimpleListFilter):
    title = '分類'
    parameter_name = 'category'

    def lookups(self, request, model_admin):
        return Article.CATEGORY_CHOICE

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(Article.category_q(self.value()))
        return queryset

class ArticleAdmin(admin.ModelAdmin):
    model = Article
    form = ArticleAdminForm
    list_filter = (ArticleCategoryListFilter,)
    search_fields = ['title']
    list_display = ('title', 'category_display', 'created', 'is_pinned')
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
        'is_data_case',
        'new_case_type',
        # 'media_url',
    )
    inlines = [CaseMediaAdmin, PostImageAdmin]

    @admin.display(description='分類')
    def category_display(self, obj):
        return obj.get_category_display()

class TagAdmin(admin.ModelAdmin):
    model = Tag
    list_display = ('name', 'sort')
    list_filter = ('name',)

class CaseTypeAdmin(admin.ModelAdmin):
    model = CaseType
    list_display = ['name', 'description']
    search_fields = ['name']
    fields = ('name', 'description')

class ArticleImageAssetAdmin(admin.ModelAdmin):
    model = ArticleImageAsset
    list_display = ('title', 'image_preview', 'public_url_display', 'created')
    search_fields = ('title',)
    readonly_fields = (
        'image_preview',
        'public_url_display',
        'markdown_display',
        'image_uuid',
        'created',
        'changed',
    )
    fields = (
        'title',
        'image',
        'image_preview',
        'public_url_display',
        'markdown_display',
        'image_uuid',
        'created',
        'changed',
    )

    def _set_request(self, request):
        self._request = request

    def _absolute_url(self, url):
        request = getattr(self, '_request', None)
        if request:
            return request.build_absolute_uri(url)
        return url

    def changelist_view(self, request, extra_context=None):
        self._set_request(request)
        return super().changelist_view(request, extra_context=extra_context)

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        self._set_request(request)
        return super().changeform_view(request, object_id, form_url, extra_context)

    @admin.display(description='預覽')
    def image_preview(self, obj):
        if not obj or not obj.image:
            return '-'
        return format_html(
            '<img src="{}" style="max-width: 240px; max-height: 160px;" />',
            obj.public_url,
        )

    @admin.display(description='對外 URL')
    def public_url_display(self, obj):
        if not obj or not obj.public_url:
            return '-'
        url = self._absolute_url(obj.public_url)
        return format_html('<a href="{0}" target="_blank" rel="noopener">{0}</a>', url)

    @admin.display(description='Markdown')
    def markdown_display(self, obj):
        if not obj or not obj.public_url:
            return '-'
        return '![large-size image]({})'.format(self._absolute_url(obj.public_url))


admin.site.register(Article, ArticleAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(CaseType, CaseTypeAdmin)
admin.site.register(ArticleImageAsset, ArticleImageAssetAdmin)
