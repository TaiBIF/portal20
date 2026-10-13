from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('page', '0020_seed_online_workshop_courses')]

    operations = [
        migrations.AddField(
            model_name='onlineworkshopcourse',
            name='video_updated_on',
            field=models.DateField('影片最後更新日期', blank=True, null=True, help_text='選填；留空時前台不顯示更新日期。'),
        ),
        migrations.AddField(
            model_name='onlineworkshopcourse',
            name='handout_updated_on',
            field=models.DateField('講義最後更新日期', blank=True, null=True, help_text='選填；留空時前台不顯示更新日期。'),
        ),
    ]
