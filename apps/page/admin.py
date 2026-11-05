from django.contrib import admin
from .models import Post, Journal, IndexBubbleSetting, NewsletterSubscription, OnlineWorkshopCourse

# Register your models here.
admin.site.register(Post)
admin.site.register(Journal)


class IndexBubbleSettingAdmin(admin.ModelAdmin):
    list_display = ("is_active", "message", "url", "updated_at")
    fields = ("is_active", "message", "url")

    def has_add_permission(self, request):
        return not IndexBubbleSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(IndexBubbleSetting, IndexBubbleSettingAdmin)


class NewsletterSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("email", "created_at")
    search_fields = ("email",)
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)


admin.site.register(NewsletterSubscription, NewsletterSubscriptionAdmin)


@admin.register(OnlineWorkshopCourse)
class OnlineWorkshopCourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'sort', 'is_active')
    list_editable = ('sort', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'title_en', 'slug', 'description')
    fieldsets = (
        ('課程內容', {'fields': ('title', 'title_en', 'slug', 'description', 'description_en')}),
        ('影片與講義', {'fields': ('video_url', 'video_updated_on', 'handout_url', 'handout_download_url', 'handout_updated_on')}),
        ('顯示設定', {'fields': ('sort', 'is_active')}),
    )
