# Generated by Django 3.2.5 on 2021-09-02 06:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0049_auto_20210831_1656'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxon',
            name='reference',
            field=models.CharField(max_length=1000, null=True, verbose_name='taieol_pic'),
        ),
    ]