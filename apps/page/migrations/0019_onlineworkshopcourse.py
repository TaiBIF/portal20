import apps.page.online_materials
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("page", "0018_newslettersubscription"),
    ]

    operations = [
        migrations.CreateModel(
            name="OnlineWorkshopCourse",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        help_text="如 standard-00；既有課程請保留此值，避免原有連結失效。",
                        max_length=100,
                        unique=True,
                        verbose_name="網址錨點",
                    ),
                ),
                ("title", models.CharField(max_length=200, verbose_name="課程名稱")),
                (
                    "title_en",
                    models.CharField(
                        blank=True, max_length=200, verbose_name="英文課程名稱"
                    ),
                ),
                ("description", models.TextField(blank=True, verbose_name="課程說明")),
                (
                    "description_en",
                    models.TextField(blank=True, verbose_name="英文課程說明"),
                ),
                (
                    "video_url",
                    models.URLField(
                        blank=True,
                        help_text="可貼上 YouTube 觀看、分享或嵌入連結，以及 Google Drive 檔案連結。",
                        max_length=1000,
                        validators=[
                            django.core.validators.URLValidator(
                                schemes=["http", "https"]
                            )
                        ],
                        verbose_name="影片連結",
                    ),
                ),
                (
                    "handout_url",
                    models.CharField(
                        blank=True,
                        help_text="可貼上 Google Drive 檔案連結、SlideShare 嵌入網址或 PDF 網址；也支援 /media/ 路徑。",
                        max_length=1000,
                        validators=[apps.page.online_materials.validate_material_link],
                        verbose_name="講義預覽連結",
                    ),
                ),
                (
                    "handout_download_url",
                    models.CharField(
                        blank=True,
                        help_text="完整網址或 /media/ 路徑；留空時使用講義預覽連結。",
                        max_length=1000,
                        validators=[apps.page.online_materials.validate_material_link],
                        verbose_name="講義開啟／下載連結",
                    ),
                ),
                ("sort", models.PositiveIntegerField(default=0, verbose_name="排序")),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="顯示於前台"),
                ),
            ],
            options={
                "verbose_name": "線上教材課程",
                "verbose_name_plural": "線上教材課程",
                "ordering": ["sort", "pk"],
            },
        ),
    ]
