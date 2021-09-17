# Generated by Django 3.2.5 on 2021-09-14 09:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0057_taxon_accepted_name_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataset',
            name='keyword',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='Dataset_Contact',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('givenname', models.CharField(blank=True, max_length=128, null=True)),
                ('surname', models.CharField(blank=True, max_length=128, null=True)),
                ('organizationname', models.CharField(blank=True, max_length=128, null=True)),
                ('positionname', models.CharField(blank=True, max_length=1024, null=True)),
                ('deliverypoint', models.CharField(blank=True, max_length=2048, null=True)),
                ('city', models.CharField(blank=True, max_length=128, null=True)),
                ('administrativearea', models.CharField(blank=True, max_length=128, null=True)),
                ('postalcode', models.CharField(blank=True, max_length=128, null=True)),
                ('country', models.CharField(blank=True, max_length=256, null=True)),
                ('phone', models.CharField(blank=True, max_length=128, null=True)),
                ('electronicmailaddress', models.CharField(blank=True, max_length=512, null=True)),
                ('onlineurl', models.CharField(blank=True, max_length=256, null=True)),
                ('role', models.CharField(blank=True, max_length=128, null=True)),
                ('creator', models.BooleanField(blank=True, default=False, null=True)),
                ('dataset', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='data.dataset')),
            ],
        ),
        migrations.CreateModel(
            name='Book_citation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identifier', models.TextField(blank=True, null=True)),
                ('citation', models.TextField(blank=True, null=True)),
                ('seq', models.TextField(blank=True, null=True)),
                ('dataset', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='data.dataset')),
            ],
        ),
    ]
