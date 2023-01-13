# Generated by Django 4.0 on 2022-12-27 07:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0083_taxon_picture'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxon_picture',
            name='class_id',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='taxon_picture',
            name='family_id',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='taxon_picture',
            name='genus_id',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='taxon_picture',
            name='kingdom_id',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='taxon_picture',
            name='order_id',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='taxon_picture',
            name='phylum_id',
            field=models.TextField(blank=True, null=True),
        ),
    ]