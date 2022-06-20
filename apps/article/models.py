import os
import uuid

from datetime import datetime

from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.urls import reverse

from conf import settings


def article_cover_path(instance, filename):
    if instance.pk:
        ext = filename.split('.')[-1].lower()
        cover_path = 'article/{}/cover_{}.{}'.format(instance.pk, instance.pk, ext)

        # delete if image name exist; or django will create a new hashed filename
        exist_path = os.path.join(settings.MEDIA_ROOT, cover_path)
        if os.path.exists(exist_path):
            os.remove(exist_path)
        return cover_path
    return ''

def images_path(instance, filename):
    if instance.post.pk: 
        ext = filename.split('.')[-1].lower()
        images_path = 'article/{}/images_{}.{}'.format(instance.post.pk, instance.image_uuid, ext)

        # delete if image name exist; or django will create a new hashed filename
        exist_path = os.path.join(settings.MEDIA_ROOT, images_path)
        if os.path.exists(exist_path):
            os.remove(exist_path)
        return images_path
    return ''

class Tag(models.Model):

    name = models.CharField(u"標籤名稱", max_length=50, blank=True)
    sort = models.PositiveIntegerField(u"排序", default=0)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u'Tag'
        verbose_name_plural = u'Tags'
        ordering = ['sort', ]



class Article(models.Model):
    CATEGORY_CHOICE = (
        ('NEWS', '新聞'),
        ('EVENT', '活動'),
        ('UPDATE', '更新'),
        ('SCI', '科普文章'),
        ('TECH', '技術專欄'),
        ('PUB', '出版品資料'),
        ('POS', 'TaiBIF發表文章/海報'),
        ('STATIC', '靜態頁面')
    )

    PINNED_CHOICE = (
        ('N', '否'),
        ('Y', '是'),
    )
    title = models.CharField('標題', max_length=500)
    content = models.TextField('內文', blank=True, help_text='新文章預設都是 markdown 顯示')
    slug = models.SlugField(unique=True, blank=True, max_length=500)
    created = models.DateTimeField('發布時間', default=timezone.now)
    changed = models.DateTimeField('修改時間', default=timezone.now)
    category = models.CharField('分類', max_length=50, choices=CATEGORY_CHOICE, default='NEWS')
    is_pinned = models.CharField('置頂', max_length=2, default='N', choices=PINNED_CHOICE)
    is_homepage = models.BooleanField('首頁專題文章', null=True)
    is_content_markdown = models.BooleanField('內文是否 markdown', null=True, blank=True, help_text='舊文章要特別勾, 才會有 markdown 顯示')
    cover = models.ImageField(upload_to=article_cover_path, blank=True, help_text='注：圖片尺寸誤過長')
    cover_license_text = models.CharField('授權文字', max_length=100, blank=True)
    tags = models.ManyToManyField(Tag, verbose_name='標籤', related_name='articles', blank=True)
    memo = models.CharField('備註(不會顯示)', max_length=128, blank=True)
    memo_text = models.TextField('備註(多字)', blank=True)

    def save(self, *args, **kwargs):
        if not self.id:
            if not self.slug:
                self.slug = slugify(self.title, allow_unicode=True)

            # prevent image save no instance.id
            saved_image = self.cover
            self.cover = None
            super(Article, self).save(*args, **kwargs)
            self.cover = saved_image
            if 'force_insert' in kwargs:
                kwargs.pop('force_insert')

        super(Article, self).save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        kwargs = {'pk': self.id}
        #if self.slug:
        #    kwargs['slug'] = self.slug
        #    return reverse('article-detail-slug', kwargs=kwargs)
        #else:
        return reverse('article-detail-id', kwargs=kwargs)

    def get_legacy_info(self):
        if 'nid:' in self.memo:
            if self.category == 'PUB':
                files = []
                for _, v in enumerate(self.memo_text.split('\n')):
                    if '__files__' not in v:
                        vlist = v.split(':')
                        files.append({
                            'url': '/media/article/download/%s'%(vlist[0]),
                            'descr': vlist[1]
                        })
                return {'files': files}
        return None

    class Meta:
        verbose_name = u'文章'
        verbose_name_plural = u'文章'
        ordering = ['-created', ]

class PostImage(models.Model):
    post = models.ForeignKey(Article, default=None, on_delete=models.CASCADE)
    image_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    images = models.ImageField(upload_to=images_path, blank=True,)
    cover_license_text = models.CharField('授權文字', max_length=100, blank=True)

    def __str__(self):
        return self.post.title
    