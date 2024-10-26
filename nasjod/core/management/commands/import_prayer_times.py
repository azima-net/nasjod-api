import json
import os
import requests
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from core.models import Address
from prayertime.models import PrayerTime
from datetime import datetime

# Constants
BASE_URL_SUNRISE = "https://www.meteo.tn/lever_coucher_gouvernorat/{date}/{state_id}/{city_id}"
STATE_ID = 359  # Sfax state ID
CITY_IDS = [540, 538, 545, 541, 539, 536, 543, 544, 537, 542, 548, 547, 632, 546, 549]

class Command(BaseCommand):
    help = "Import prayer times and sunrise data from a JSON file and populate the database."

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help="The path to the JSON file containing prayer times.")

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File {file_path} does not exist."))
            return

        # Open and load the JSON file
        with open(file_path, 'r') as json_file:
            prayer_times_data = json.load(json_file)

        # Iterate over each governorate and city
        for governorate_name, cities in prayer_times_data.items():
            for city_name, city_data in cities.items():
                # Check if the address exists, otherwise create it
                latitude = float(city_data['latitude'])
                longitude = float(city_data['longitude'])
                coordinates = Point(longitude, latitude)  # Longitude first in Point

                address, created = Address.objects.get_or_create(
                    city=city_name,
                    state=governorate_name,
                    country="Tunisia",  # Assuming country is Tunisia for all
                    coordinates=coordinates,
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created new address for {city_name}, {governorate_name}"))
                else:
                    self.stdout.write(f"Address for {city_name}, {governorate_name} already exists.")

                # Iterate over each prayer time entry for the city
                for prayer_time_entry in city_data['prayer_times']:
                    # Convert string dates and times to Python datetime and time objects
                    date_str = prayer_time_entry['date']
                    date = datetime.strptime(date_str, "%Y-%m-%d %H:%M")

                    fajr_time = datetime.strptime(prayer_time_entry['sobh'], "%H:%M").time()
                    dhuhr_time = datetime.strptime(prayer_time_entry['dhohr'], "%H:%M").time()
                    asr_time = datetime.strptime(prayer_time_entry['aser'], "%H:%M").time()
                    maghrib_time = datetime.strptime(prayer_time_entry['magreb'], "%H:%M").time()
                    isha_time = datetime.strptime(prayer_time_entry['isha'], "%H:%M").time()
                    sunrise_time = datetime.strptime(prayer_time_entry['sunrise'], "%H:%M").time()

                    # Create or get the PrayerTime for this address and date
                    prayer_time, created = PrayerTime.objects.get_or_create(
                        location=address,
                        date=date,
                        defaults={
                            'fajr': fajr_time,
                            'sunrise': sunrise_time,  # Add sunrise to defaults
                            'dhuhr': dhuhr_time,
                            'asr': asr_time,
                            'maghrib': maghrib_time,
                            'isha': isha_time
                        }
                    )

                    if created:
                        self.stdout.write(self.style.SUCCESS(f"Created new PrayerTime for {city_name} on {date_str}."))
                    else:
                        self.stdout.write(f"PrayerTime for {city_name} on {date_str} already exists.")
