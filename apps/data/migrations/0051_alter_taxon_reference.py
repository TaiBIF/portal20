# Generated by Django 3.2.5 on 2021-09-02 06:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0050_taxon_reference'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxon',
            name='reference',
            field=models.CharField(max_length=2000, null=True, verbose_name='taieol_pic'),
        ),
    ]