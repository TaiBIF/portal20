# Generated by Django 3.2.5 on 2021-09-02 07:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0053_alter_taxon_reference'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxon',
            name='reference',
            field=models.CharField(max_length=5000, null=True, verbose_name='reference'),
        ),
    ]
