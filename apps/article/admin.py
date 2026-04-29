from django.contrib import admin
from django import forms

from .models import Article, Tag, PostImage, CaseType, CaseMedia

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


admin.site.register(Article, ArticleAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(CaseType, CaseTypeAdmin)
