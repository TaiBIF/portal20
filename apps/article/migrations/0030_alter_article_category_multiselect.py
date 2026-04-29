# Generated manually for storing multiple article categories in one field.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('article', '0029_alter_casemedia_post'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='category',
            field=models.CharField(default='NEWS', max_length=255, verbose_name='分類'),
        ),
    ]
