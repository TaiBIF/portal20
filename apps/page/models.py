import os
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



class Post(models.Model):
    title = models.CharField(u"網站名稱", max_length=200, default="")
    upload = models.ImageField(upload_to= page_image_path, blank=True)
    url = models.URLField(u"網站", max_length = 200, default="")
    content = models.CharField(u"內容", max_length=200, default="",blank=True)
    sort = models.PositiveIntegerField(u"排序", default=0)
    cat = models.CharField(u"網站類型", max_length=200, default="", blank=True)

    def __str__(self):
        return self.title


class Journal(models.Model):
    title = models.CharField(u"網站名稱", max_length=200, default="")
    upload = models.ImageField(upload_to= page_image_path, blank=True)
    url = models.URLField(u"網站", max_length = 200, default="")
    content = models.CharField(u"內容", max_length=200, default="",blank=True)
    sort = models.PositiveIntegerField(u"排序", default=0)
    

    def __str__(self):
        return self.title


   

