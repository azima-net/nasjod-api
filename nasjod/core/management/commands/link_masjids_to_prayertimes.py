from django.core.management.base import BaseCommand
from django.db import transaction
from masjid.models import Masjid
from prayertime.models import PrayerTime

class Command(BaseCommand):
    help = "Link all masjids to prayer times based on matching state."

    def handle(self, *args, **kwargs):
        # Track the number of masjids and prayer times linked
        linked_count = 0

        # Iterate through each masjid and attempt to link it to prayer times by state
        for masjid in Masjid.objects.all():
            state = masjid.address.state if masjid.address else None
            if not state:
                self.stdout.write(self.style.WARNING(f"Masjid '{masjid.name}' has no address or state. Skipping..."))
                continue

            # Find prayer times matching the masjid's state
            prayer_times = PrayerTime.objects.filter(location__state=state)

            if prayer_times.exists():
                with transaction.atomic():  # Use a transaction for atomic updates
                    for prayer_time in prayer_times:
                        prayer_time.masjids.add(masjid)
                    linked_count += prayer_times.count()
                    self.stdout.write(
                        self.style.SUCCESS(f"Linked Masjid '{masjid.name}' to {prayer_times.count()} prayer times in '{state}'")
                    )
            else:
                self.stdout.write(self.style.WARNING(f"No prayer times found for state '{state}' to link with Masjid '{masjid.name}'"))

        # Summary of results
        self.stdout.write(self.style.SUCCESS(f"Total prayer times linked to masjids: {linked_count}"))
