# Generated by Django 3.0.1 on 2020-02-13 06:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0019_auto_20200211_1512'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataset',
            name='status',
            field=models.CharField(choices=[('Public', 'Public'), ('Private', 'Private')], max_length=10, verbose_name='status'),
        ),
    ]