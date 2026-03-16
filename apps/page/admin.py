from django.contrib import admin
from .models import Post, Journal, IndexBubbleSetting

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
