# Generated by Django 3.0.1 on 2020-02-18 02:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('page', '0006_post_cat'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='cat',
            field=models.CharField(default='', max_length=200, null=True, verbose_name='網站類型'),
        ),
    ]
