import os
from datetime import datetime

from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from conf import settings


def article_cover_path(instance, filename):
    ext = filename.split('.')[-1].lower()
    cover_path = 'article/{}/cover_{}.{}'.format(instance.pk, instance.pk, ext)

    # delete if image name exist; or django will create a new hashed filename
    exist_path = os.path.join(settings.MEDIA_ROOT, cover_path)
    if os.path.exists(exist_path):
        os.remove(exist_path)
    return cover_path


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
    content = models.TextField('內文', blank=True)
    slug = models.SlugField(unique=True, blank=True, max_length=500)
    created = models.DateTimeField('發佈時間', default=timezone.now)
    changed = models.DateTimeField('修改時間', default=timezone.now)
    category = models.CharField(u"分類", max_length=50, choices=CATEGORY_CHOICE, default='NEWS')
    is_pinned = models.CharField(u"置頂", max_length=2, default='N', choices=PINNED_CHOICE)
    cover = models.ImageField(upload_to=article_cover_path, blank=True)
    cover_license_text = models.CharField('授權文字', max_length=100, blank=True)
    tags = models.ManyToManyField(Tag, verbose_name=u"標籤", related_name='articles', blank=True)
    memo = models.CharField('備註(不會顯示)', max_length=128, blank=True)
    memo_text = models.TextField('備註(多字)', blank=True)

    def save(self, *args, **kwargs):
        if not self.id and not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super(Article, self).save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return '/article/%s/' % self.slug

    def get_legacy_info(self):
        if 'nid:' in self.memo:
            if self.category == 'PUB':
                files = []
                for _, v in enumerate(self.memo_text.split('\n')):
                    if '__files__' not in v:
                        vlist = v.split(':')
                        files.append({
                            'url': '/PATH/TO/%s'%(vlist[0]),
                            'descr': vlist[1]
                        })
                return {'files': files}
        return None

    class Meta:
        verbose_name = u'文章'
        verbose_name_plural = u'文章'
        ordering = ['-created', ]
