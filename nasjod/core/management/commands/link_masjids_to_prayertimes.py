from django.core.management.base import BaseCommand
from django.db import transaction
from masjid.models import Masjid
from prayertime.models import PrayerTime

class Command(BaseCommand):
    help = "Link all masjids to prayer times based on matching city."

    def handle(self, *args, **kwargs):
        # Track the number of masjids and prayer times linked
        linked_count = 0

        # Iterate through each masjid and attempt to link it to prayer times by city
        for masjid in Masjid.objects.all():
            city = masjid.address.city if masjid.address else None
            if not city:
                self.stdout.write(self.style.WARNING(f"Masjid '{masjid.name}' has no address or city. Skipping..."))
                continue

            # Find prayer times matching the masjid's city
            prayer_times = PrayerTime.objects.filter(location__city=city)

            if prayer_times.exists():
                with transaction.atomic():  # Use a transaction for atomic updates
                    for prayer_time in prayer_times:
                        prayer_time.masjids.add(masjid)
                    linked_count += prayer_times.count()
                    self.stdout.write(
                        self.style.SUCCESS(f"Linked Masjid '{masjid.name}' to {prayer_times.count()} prayer times in '{city}'")
                    )
            else:
                self.stdout.write(self.style.WARNING(f"No prayer times found for city '{city}' to link with Masjid '{masjid.name}'"))

        # Summary of results
        self.stdout.write(self.style.SUCCESS(f"Total prayer times linked to masjids: {linked_count}"))
