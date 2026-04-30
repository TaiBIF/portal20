import uuid

import apps.article.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('article', '0030_alter_article_category_multiselect'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArticleImageAsset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=200, verbose_name='圖片名稱')),
                ('image_uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('image', models.ImageField(upload_to=apps.article.models.article_image_asset_path, verbose_name='圖片')),
                ('alt_text', models.CharField(blank=True, max_length=200, verbose_name='替代文字')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='建立時間')),
                ('changed', models.DateTimeField(auto_now=True, verbose_name='修改時間')),
            ],
            options={
                'verbose_name': '文章圖片',
                'verbose_name_plural': '文章圖片',
                'ordering': ['-created'],
            },
        ),
    ]
