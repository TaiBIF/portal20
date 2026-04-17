import os
import uuid
from datetime import datetime

from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from conf import settings


# Create your models here.
def page_image_path(instance, filename):
    ext = filename.split('.')[-1].lower()
    cover_path = 'page/{}/cover_{}.{}'.format(instance.pk, instance.pk, ext)

    # delete if image name exist; or django will create a new hashed filename
    exist_path = os.path.join(settings.MEDIA_ROOT, cover_path)
    if os.path.exists(exist_path):
        os.remove(exist_path)

    return cover_path

def upload_image_path(instance, filename):
    ext = filename.split('.')[-1].lower()
    unique_id = uuid.uuid4().hex

    return f'page/journal/{unique_id}/image.{ext}'



class Post(models.Model):
    CATEGORY_CHOICE = (
        ('web', '網站'),
        ('data', '資料庫'),
    )

    title = models.CharField(u"網站名稱", max_length=200, default="")
    title_en = models.CharField(u"網站英文名稱", max_length=200, default="")
    Upload = models.ImageField(upload_to= page_image_path, blank=True)
    url = models.URLField(u"網站", max_length = 200, default="")
    content = models.CharField(u"內容", max_length=200, default="",blank=True)
    content_en = models.CharField(u"英文說明", max_length=200, default="",blank=True)
    sort = models.PositiveIntegerField(u"排序", default=0)
    cat = models.CharField(u"網站類型", max_length=200, choices=CATEGORY_CHOICE, default="", blank=True)

    def __str__(self):
        return self.title
    
    class Meta:
        ordering =  ['sort',]
        verbose_name = u'相關連結'
        verbose_name_plural = u'相關連結'


class Journal(models.Model):
    title = models.CharField(u"網站名稱", max_length=200, default="")
    title_en = models.CharField(u"網站英文名稱", max_length=200, default="")
    upload = models.ImageField(upload_to=upload_image_path, blank=True)
    url = models.URLField(u"網站", max_length = 200, default="")
    content = models.CharField(u"內容", max_length=200, default="",blank=True)
    content_en = models.CharField(u"英文說明", max_length=200, default="",blank=True)
    sort = models.PositiveIntegerField(u"排序", default=0)
    

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = u'資料論文/期刊'
        verbose_name_plural = u'資料論文/期刊'
        ordering = ['sort',]


class IndexBubbleSetting(models.Model):
    message = models.CharField(u"說話魚文案", max_length=300, default="活動資訊活動資訊活動資訊活動資訊活動資訊活動資訊活動資訊活動資訊")
    url = models.CharField(
        u"說話魚連結",
        max_length=500,
        blank=True,
        default="",
        help_text=u"可使用站內路徑（如 /zh-hant/open-process）或完整網址"
    )
    is_active = models.BooleanField(u"啟用", default=True)
    updated_at = models.DateTimeField(u"更新時間", auto_now=True)

    def __str__(self):
        return self.message

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={
                "message": "活動資訊活動資訊活動資訊活動資訊活動資訊活動資訊活動資訊活動資訊",
                "url": "#",
            },
        )
        return obj

    class Meta:
        verbose_name = u'首頁說話魚設定'
        verbose_name_plural = u'首頁說話魚設定'


class NewsletterSubscription(models.Model):
    email = models.EmailField(u"電子信箱", max_length=254, unique=True)
    created_at = models.DateTimeField(u"訂閱時間", auto_now_add=True)

    def __str__(self):
        return self.email

    class Meta:
        ordering = ["-created_at"]
        verbose_name = u"電子報訂閱名單"
        verbose_name_plural = u"電子報訂閱名單"
