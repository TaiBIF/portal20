# Generated by Django 3.2.5 on 2021-09-27 12:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0063_auto_20210927_1932'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datasetorganization',
            name='description',
            field=models.TextField(default='', null=True, verbose_name='description'),
        ),
    ]
