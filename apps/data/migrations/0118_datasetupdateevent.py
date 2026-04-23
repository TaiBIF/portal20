from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("data", "0117_alter_workshopcertificationlist_level"),
    ]

    operations = [
        migrations.CreateModel(
            name="DatasetUpdateEvent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("dataset_mod_date", models.DateTimeField(verbose_name="資料集異動時間")),
                (
                    "captured_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="快照建立時間"),
                ),
                ("source", models.TextField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        blank=True,
                        choices=[("PUBLIC", "公開"), ("PRIVATE", "非公開")],
                        max_length=10,
                        null=True,
                        verbose_name="狀態",
                    ),
                ),
                ("taibif_dataset_id", models.UUIDField()),
                ("dataset_title", models.CharField(blank=True, max_length=300, null=True)),
                ("dataset_name", models.CharField(blank=True, max_length=300, null=True)),
                ("organization_name", models.TextField(blank=True, null=True)),
                ("dwc_core_type", models.CharField(blank=True, max_length=128, null=True)),
                (
                    "dataset",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="update_events",
                        to="data.dataset",
                    ),
                ),
            ],
            options={
                "verbose_name": "資料集更新事件",
                "verbose_name_plural": "資料集更新事件",
            },
        ),
        migrations.AddConstraint(
            model_name="datasetupdateevent",
            constraint=models.UniqueConstraint(
                fields=("dataset", "dataset_mod_date"),
                name="uniq_dataset_mod_date_event",
            ),
        ),
        migrations.AddIndex(
            model_name="datasetupdateevent",
            index=models.Index(fields=["dataset_mod_date"], name="idx_ds_evt_mod_date"),
        ),
        migrations.AddIndex(
            model_name="datasetupdateevent",
            index=models.Index(fields=["captured_at"], name="idx_ds_evt_captured"),
        ),
    ]
