# Generated by Django 3.2.5 on 2021-09-27 12:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0065_auto_20210927_2017'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datasetorganization',
            name='country_code',
            field=models.CharField(default='TW', max_length=8, null=True, verbose_name='country_code'),
        ),
    ]
