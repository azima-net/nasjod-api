import json
from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_date
from masjid.models import Masjid, PrayerTime
from django.core.files.storage import default_storage

class Command(BaseCommand):
    help = 'Add prayer times to all masjids in the specified state from a JSON file stored in Cloudflare R2.'

    def add_arguments(self, parser):
        parser.add_argument('state', type=str, help='The state for which to add prayer times')
        parser.add_argument('file_path', type=str, help='Path to the JSON file in Cloudflare R2')

    def handle(self, *args, **options):
        state = options['state']
        file_path = options['file_path']

        try:
            # Use Django's default storage to open the file
            with default_storage.open(file_path) as file:
                prayer_times_data = json.load(file)
        except Exception as e:
            raise CommandError(f'Failed to fetch or read the file from Cloudflare R2: {e}')

        masjids = Masjid.objects.filter(address__state__iexact=state)
        if not masjids.exists():
            self.stdout.write(self.style.WARNING(f'No masjids found in the state "{state}"'))
            return

        for date_str, data in prayer_times_data.items():
            if data.get('code') != 200:
                self.stdout.write(self.style.ERROR(f"Error in data for date {date_str}: {data.get('status')}"))
                continue

            timings = data['data']['timings']
            date = parse_date(date_str)

            for masjid in masjids:
                PrayerTime.objects.update_or_create(
                    masjid=masjid,
                    date=date,
                    defaults={
                        'fajr': timings['Fajr'],
                        'sunrise': timings['Sunrise'],
                        'dhuhr': timings['Dhuhr'],
                        'asr': timings['Asr'],
                        'maghrib': timings['Maghrib'],
                        'isha': timings['Isha'],
                    }
                )

        self.stdout.write(self.style.SUCCESS(f'Prayer times successfully added for state "{state}"'))
