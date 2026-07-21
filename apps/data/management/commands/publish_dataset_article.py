from datetime import date, datetime, time

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.data.helpers.publish_dataset_article import (
    previous_month,
    publish_dataset_article,
)


class Command(BaseCommand):
    help = "Publish the monthly TaiBIF dataset update article."

    def add_arguments(self, parser):
        target_group = parser.add_mutually_exclusive_group()
        target_group.add_argument(
            "--target-month",
            help="Target month in YYYY-MM format, for example 2026-06.",
        )
        target_group.add_argument(
            "--previous-month",
            action="store_true",
            help="Publish for the month before today. This is the default.",
        )
        parser.add_argument("--year", type=int, help="Target year, for example 2026.")
        parser.add_argument("--month", type=int, help="Target month, 1-12.")
        parser.add_argument(
            "--force",
            action="store_true",
            help="Update the existing article if one already exists.",
        )
        parser.add_argument(
            "--created-at",
            help="Article publish datetime in ISO format. Defaults to now.",
        )

    def handle(self, *args, **options):
        year, month = self.get_target_year_month(options)
        created_at = self.get_created_at(options["created_at"])

        result = publish_dataset_article(
            year,
            month,
            force=options["force"],
            created_at=created_at,
        )

        if result.status in {"created", "updated"}:
            self.stdout.write(self.style.SUCCESS(result.message))
        else:
            self.stdout.write(result.message)

    def get_target_year_month(self, options):
        if options["target_month"]:
            if options["year"] is not None or options["month"] is not None:
                raise CommandError("--target-month 不可和 --year/--month 同時指定。")
            try:
                year_text, month_text = options["target_month"].split("-", 1)
                year = int(year_text)
                month = int(month_text)
            except ValueError as exc:
                raise CommandError("--target-month 格式需為 YYYY-MM，例如 2026-06。") from exc
            self.validate_month(month)
            return year, month

        if options["year"] is not None or options["month"] is not None:
            if options["previous_month"]:
                raise CommandError("--previous-month 不可和 --year/--month 同時指定。")
            if options["year"] is None or options["month"] is None:
                raise CommandError("--year 和 --month 需要一起指定。")
            self.validate_month(options["month"])
            return options["year"], options["month"]

        return previous_month()

    def get_created_at(self, value):
        if not value:
            return None

        parsed = parse_datetime(value)
        if parsed is None:
            try:
                parsed_date = date.fromisoformat(value)
            except ValueError as exc:
                raise CommandError("--created-at 格式需為 ISO 日期或時間，例如 2026-07-01T00:10:00。") from exc
            parsed = timezone.make_aware(datetime.combine(parsed_date, time.min))

        if timezone.is_naive(parsed):
            parsed = timezone.make_aware(parsed)
        return parsed

    def validate_month(self, month):
        if month < 1 or month > 12:
            raise CommandError("--month 需介於 1 到 12。")
