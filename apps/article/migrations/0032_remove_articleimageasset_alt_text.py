from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('article', '0031_articleimageasset'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='articleimageasset',
            name='alt_text',
        ),
    ]
