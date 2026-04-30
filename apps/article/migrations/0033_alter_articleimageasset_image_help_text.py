import apps.article.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("article", "0032_remove_articleimageasset_alt_text"),
    ]

    operations = [
        migrations.AlterField(
            model_name="articleimageasset",
            name="image",
            field=models.ImageField(
                help_text="可上傳 JPG、PNG、WebP 圖片；儲存時會自動修正方向、將最長邊壓縮至 1600px，並覆寫為壓縮後的圖片。",
                upload_to=apps.article.models.article_image_asset_path,
                verbose_name="圖片",
            ),
        ),
    ]
