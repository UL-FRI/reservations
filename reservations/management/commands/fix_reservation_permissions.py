from datetime import datetime

from django.core.management.base import BaseCommand, CommandParser
from reservations.models import Reservation
from reservations.permissions import sync_reservation_owner_permissions


class Command(BaseCommand):
    """Scan reservations and fix owner permissions that are out of sync."""

    help = __doc__

    def add_arguments(self, parser: CommandParser) -> None:
        """Add command line arguments."""
        parser.add_argument(
            "--start-date",
            type=datetime.fromisoformat,
            default=None,
            help="Only scan reservations starting on or after this ISO date/datetime.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would change without modifying any permissions.",
        )

    def handle(self, *args, **options) -> None:
        """Scan reservations and sync owner permissions."""
        start_date = options["start_date"]
        dry_run = options["dry_run"]

        reservations = Reservation.objects.order_by("pk")
        if start_date is not None:
            reservations = reservations.filter(start__gte=start_date)

        total_changes = 0
        changed_reservations = 0
        for reservation in reservations.iterator():
            changes = sync_reservation_owner_permissions(reservation, dry_run=dry_run)
            if changes:
                changed_reservations += 1
                total_changes += len(changes)
                for change in changes:
                    self.stdout.write(change)

        verb = "Would change" if dry_run else "Changed"
        self.stdout.write(self.style.SUCCESS(
            f"{verb} {total_changes} permission(s) on {changed_reservations} reservation(s) "
            f"(out of {reservations.count()} scanned)."
        ))
