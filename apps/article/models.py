import os
import uuid

from datetime import datetime

from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify
from django.urls import reverse
from PIL import Image, ImageOps

from conf import settings


def article_cover_path(instance, filename):
    if instance.pk:
        ext = filename.split(".")[-1].lower()
        cover_path = "article/{}/cover_{}.{}".format(instance.pk, instance.pk, ext)

        # delete if image name exist; or django will create a new hashed filename
        exist_path = os.path.join(settings.MEDIA_ROOT, cover_path)
        if os.path.exists(exist_path):
            os.remove(exist_path)
        return cover_path
    return ""


def images_path(instance, filename):
    if instance.post.pk:
        ext = filename.split(".")[-1].lower()
        images_path = "article/{}/images_{}.{}".format(
            instance.post.pk, instance.image_uuid, ext
        )

        # delete if image name exist; or django will create a new hashed filename
        exist_path = os.path.join(settings.MEDIA_ROOT, images_path)
        if os.path.exists(exist_path):
            os.remove(exist_path)
        return images_path
    return ""


def article_image_asset_path(instance, filename):
    ext = filename.split(".")[-1].lower()
    return "article/images/library/{}.{}".format(instance.image_uuid, ext)


class Tag(models.Model):

    name = models.CharField("標籤名稱", max_length=50, blank=True)
    sort = models.PositiveIntegerField("排序", default=0)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = [
            "sort",
        ]


class CaseType(models.Model):
    name = models.CharField("案例類型名稱", max_length=100)
    description = models.TextField("描述", blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "應用案例類型"
        verbose_name_plural = "應用案例類型"


class Article(models.Model):
    CATEGORY_CHOICE = (
        ("NEWS", "新聞"),
        ("EVENT", "活動"),
        ("SCI", "科普"),
        ("PUB", "出版品"),
        ("POS", "TaiBIF 成果"),
        ("STORY", "資料故事"),
    )

    PINNED_CHOICE = (
        ("N", "否"),
        ("Y", "是"),
    )

    CASE_TYPE_CHOICE = (("DATATHON", "數據松"),)

    title = models.CharField("標題", max_length=500)
    summary = models.TextField("摘要", blank=True)
    content = models.TextField(
        "內文", blank=True, help_text="新文章預設都是 markdown 顯示"
    )
    slug = models.SlugField(unique=True, blank=True, max_length=500)
    created = models.DateTimeField("發布時間", default=timezone.now)
    changed = models.DateTimeField("修改時間", default=timezone.now)
    category = models.CharField("分類", max_length=255, default="NEWS")
    is_pinned = models.CharField(
        "置頂", max_length=2, default="N", choices=PINNED_CHOICE
    )
    is_homepage = models.BooleanField("首頁專題文章", null=True)
    is_content_markdown = models.BooleanField(
        "內文是否 markdown",
        null=True,
        blank=True,
        help_text="舊文章要特別勾, 才會有 markdown 顯示",
    )
    cover = models.ImageField(
        upload_to=article_cover_path, blank=True, help_text="注：圖片尺寸勿過長"
    )
    cover_license_text = models.CharField("授權文字", max_length=100, blank=True)
    tags = models.ManyToManyField(
        Tag, verbose_name="標籤", related_name="articles", blank=True
    )
    memo = models.CharField("備註(不會顯示)", max_length=128, blank=True)
    memo_text = models.TextField("備註(多字)", blank=True)
    is_data_case = models.BooleanField(
        "是否為應用案例",
        default=False,
        help_text="（勾選後才會呈現在 資料應用案例 頁面上）",
    )
    media_url = models.TextField("多媒體檔案連結", blank=True)
    case_type = models.CharField(
        "案例類型",
        max_length=50,
        choices=CASE_TYPE_CHOICE,
        blank=True,
        help_text="（若為以上應用案例打勾，請選擇案例類型）",
    )
    new_case_type = models.ForeignKey(
        CaseType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="（若為以上應用案例打勾，請選擇案例類型）",
        verbose_name="應用案例類型",
    )

    def save(self, *args, **kwargs):
        self.category = self.normalize_category_value(self.category)

        if not self.id:
            if not self.slug:
                self.slug = slugify(self.title, allow_unicode=True)

            # prevent image save no instance.id
            saved_image = self.cover
            self.cover = None
            super(Article, self).save(*args, **kwargs)
            self.cover = saved_image
            if "force_insert" in kwargs:
                kwargs.pop("force_insert")

        super(Article, self).save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        kwargs = {"pk": self.id}
        # if self.slug:
        #    kwargs['slug'] = self.slug
        #    return reverse('article-detail-slug', kwargs=kwargs)
        # else:
        return reverse("article-detail-id", kwargs=kwargs)

    @classmethod
    def normalize_category_value(cls, value):
        if isinstance(value, (list, tuple, set)):
            values = value
        else:
            values = str(value or "").split(",")

        normalized = []
        for category in values:
            category = str(category).strip().upper()
            if category and category not in normalized:
                normalized.append(category)

        return ",".join(normalized) or "NEWS"

    @classmethod
    def category_q(cls, categories):
        if isinstance(categories, str):
            categories = [categories]

        query = Q()
        for category in categories:
            category = str(category).strip().upper()
            if not category:
                continue

            query |= (
                Q(category=category)
                | Q(category__startswith=f"{category},")
                | Q(category__endswith=f",{category}")
                | Q(category__contains=f",{category},")
            )

        return query

    @property
    def category_list(self):
        return self.normalize_category_value(self.category).split(",")

    @property
    def primary_category(self):
        return self.category_list[0]

    def has_category(self, category):
        return str(category).strip().upper() in self.category_list

    def get_category_display(self):
        label_map = dict(self.CATEGORY_CHOICE)
        return "、".join(
            label_map.get(category, category) for category in self.category_list
        )

    def get_legacy_info(self):
        if "nid:" in self.memo:
            if self.has_category("PUB"):
                files = []
                for _, v in enumerate(self.memo_text.split("\n")):
                    if "__files__" not in v:
                        vlist = v.split(":")
                        files.append(
                            {
                                "url": "/media/article/download/%s" % (vlist[0]),
                                "descr": vlist[1],
                            }
                        )
                return {"files": files}
        return None

    class Meta:
        verbose_name = "文章"
        verbose_name_plural = "文章"
        ordering = [
            "-created",
        ]


class PostImage(models.Model):
    post = models.ForeignKey(Article, default=None, on_delete=models.CASCADE)
    image_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    images = models.ImageField(
        upload_to=images_path,
        blank=True,
    )
    cover_license_text = models.CharField("授權文字", max_length=100, blank=True)

    def __str__(self):
        return self.post.title


class ArticleImageAsset(models.Model):
    MAX_IMAGE_SIZE = (1600, 1600)
    JPEG_QUALITY = 85

    title = models.CharField("圖片名稱", max_length=200, blank=True)
    image_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    image = models.ImageField(
        "圖片",
        upload_to=article_image_asset_path,
        help_text="可上傳 JPG、PNG、WebP 圖片；儲存時會自動修正方向、將最長邊壓縮至 1600px，並覆寫為壓縮後的圖片。",
    )
    created = models.DateTimeField("建立時間", auto_now_add=True)
    changed = models.DateTimeField("修改時間", auto_now=True)

    def __str__(self):
        if self.title:
            return self.title
        return str(self.image_uuid)

    @property
    def public_url(self):
        if self.image:
            return self.image.url
        return ""

    @property
    def markdown(self):
        if not self.public_url:
            return ""
        return "![large-size image]({})".format(self.public_url)

    def save(self, *args, **kwargs):
        super(ArticleImageAsset, self).save(*args, **kwargs)
        self.compress_image()

    def compress_image(self):
        if not self.image:
            return

        try:
            image_path = self.image.path
        except NotImplementedError:
            return

        if not os.path.exists(image_path):
            return

        with Image.open(image_path) as image:
            image_format = image.format
            if image_format not in ("JPEG", "PNG", "WEBP"):
                return

            image = ImageOps.exif_transpose(image)
            image.thumbnail(self.MAX_IMAGE_SIZE, Image.LANCZOS)
            save_kwargs = {"optimize": True}

            if image_format == "JPEG":
                save_kwargs["quality"] = self.JPEG_QUALITY
                if image.mode in ("RGBA", "LA", "P"):
                    background = Image.new("RGB", image.size, (255, 255, 255))
                    if image.mode == "P":
                        image = image.convert("RGBA")
                    background.paste(image, mask=image.split()[-1])
                    image = background
                elif image.mode != "RGB":
                    image = image.convert("RGB")
            elif image_format == "PNG":
                save_kwargs["compress_level"] = 9
            elif image_format == "WEBP":
                save_kwargs["quality"] = self.JPEG_QUALITY

            image.load()
            image.save(image_path, image_format, **save_kwargs)

    class Meta:
        verbose_name = "文章圖片"
        verbose_name_plural = "文章圖片"
        ordering = ["-created"]


class CaseMedia(models.Model):
    post = models.ForeignKey(
        Article, default=None, on_delete=models.CASCADE, related_name="case_media"
    )
    media_name = models.CharField("多媒體名稱", max_length=128, blank=True)
    media_url = models.CharField("多媒體檔案連結", max_length=500, blank=True)

    class Meta:
        verbose_name = "案例多媒體"
        verbose_name_plural = "案例多媒體"
