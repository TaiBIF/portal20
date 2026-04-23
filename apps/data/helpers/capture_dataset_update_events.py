"""
Usage:
    python manage.py shell < ./apps/data/helpers/capture_dataset_update_events.py

This script records dataset update events for monthly-status history.
One event row is stored per (dataset, dataset_mod_date) pair.
"""

from django.db import transaction
from django.db.models import Max
from apps.data.models import Dataset, DatasetUpdateEvent


def main():
    datasets = (
        Dataset.objects.filter(
            source="TaiBIF IPT",
            status="PUBLIC",
        )
        .exclude(mod_date__isnull=True)
        .values(
            "id",
            "taibif_dataset_id",
            "title",
            "name",
            "organization_name",
            "dwc_core_type",
            "source",
            "status",
            "mod_date",
        )
    )

    latest_event_mod_dates = dict(
        DatasetUpdateEvent.objects.values("dataset_id")
        .annotate(latest_mod_date=Max("dataset_mod_date"))
        .values_list("dataset_id", "latest_mod_date")
    )

    to_create = []
    for row in datasets:
        latest_mod_date = latest_event_mod_dates.get(row["id"])
        if latest_mod_date == row["mod_date"]:
            continue

        to_create.append(
            DatasetUpdateEvent(
                dataset_id=row["id"],
                dataset_mod_date=row["mod_date"],
                source=row["source"],
                status=row["status"],
                taibif_dataset_id=row["taibif_dataset_id"],
                dataset_title=row["title"],
                dataset_name=row["name"],
                organization_name=row["organization_name"],
                dwc_core_type=row["dwc_core_type"],
            )
        )

    with transaction.atomic():
        DatasetUpdateEvent.objects.bulk_create(to_create, ignore_conflicts=True)

    print(
        f"Dataset update event capture completed. "
        f"scanned={len(datasets)}, inserted={len(to_create)}, skipped={len(datasets) - len(to_create)}"
    )


main()
