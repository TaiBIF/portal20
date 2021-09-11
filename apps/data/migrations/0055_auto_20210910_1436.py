# Generated by Django 3.2.5 on 2021-09-10 06:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0054_alter_taxon_reference'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxon',
            name='classKey',
            field=models.IntegerField(default=0, null=True, verbose_name='classKey'),
        ),
        migrations.AddField(
            model_name='taxon',
            name='familyKey',
            field=models.IntegerField(default=0, null=True, verbose_name='familyKey'),
        ),
        migrations.AddField(
            model_name='taxon',
            name='genusKey',
            field=models.IntegerField(default=0, null=True, verbose_name='genusKey'),
        ),
        migrations.AddField(
            model_name='taxon',
            name='kingdomKey',
            field=models.IntegerField(default=0, null=True, verbose_name='kingdomKey'),
        ),
        migrations.AddField(
            model_name='taxon',
            name='orderKey',
            field=models.IntegerField(default=0, null=True, verbose_name='orderKey'),
        ),
        migrations.AddField(
            model_name='taxon',
            name='phylumKey',
            field=models.IntegerField(default=0, null=True, verbose_name='phylumKey'),
        ),
    ]
