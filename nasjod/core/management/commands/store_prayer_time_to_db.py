import json
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from django.core.files.storage import default_storage
from core.models import Address
from prayertime.models import PrayerTime
from django.db import transaction

MAX_WORKERS = 10
GOUVERNORAT = "sfax"
FILENAME = "tunisia-sfax-prayer-times.json"


class Command(BaseCommand):
    help = "Fetch prayer times from block storage and store them directly into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            '--gouvernorat',
            type=str,
            default=GOUVERNORAT,
            help='gouvernorat to fetch its prayertimes'
        )
        parser.add_argument(
            '--max-workers',
            type=int,
            default=MAX_WORKERS,
            help='Maximum number of threads for concurrent requests.'
        )

    def handle(self, *args, **options):
        gouvernorat = options['gouvernorat']
        max_workers = options['max_workers']
        filename = f"tunisia-{gouvernorat}-prayer-times.json"
        prayer_times_data = self.get_file_as_dict(filename)
        self.store_data(prayer_times_data)
    
    def get_file_as_dict(self, file_path):
        """
        Retrieve a file from block storage and load it as a dictionary.

        :param file_path: Path of the file in block storage.
        :return: A dictionary containing the data from the file.
        :raises: FileNotFoundError if the file does not exist, ValueError for invalid JSON.
        """
        try:
            # Check if the file exists in storage
            if not default_storage.exists(file_path):
                raise FileNotFoundError(f"File '{file_path}' does not exist in block storage.")

            # Open the file and read its content
            with default_storage.open(file_path, 'r') as file:
                content = file.read()

            # Parse JSON content into a dictionary
            data_dict = json.loads(content)
            return data_dict

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON content in file '{file_path}': {str(e)}")
        except Exception as e:
            raise RuntimeError(f"An error occurred while retrieving the file: {str(e)}")

    def store_data(self, prayer_times_data):
        """
        Stores the merged prayer times data into the database.
        """
        with transaction.atomic():
            for gov_name, cities in prayer_times_data.items():
                for city_name, city_info in cities.items():
                    latitude = float(city_info['latitude'])
                    longitude = float(city_info['longitude'])
                    coordinates = Point(longitude, latitude)  # Longitude first

                    # Create a new Address entry every time (as requested)
                    try:
                        address = Address.objects.create(
                            city=city_name,
                            state=gov_name,
                            country="Tunisia",
                            coordinates=coordinates
                        )
                        self.stdout.write(self.style.SUCCESS(f"Created new address for {city_name}, {gov_name}."))
                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f"Error creating Address for {city_name}, {gov_name}: {e}"))
                        continue

                    for prayer_time_entry in city_info['prayer_times']:
                        try:
                            date_str = prayer_time_entry['date']
                            # Attempt parsing date with time
                            try:
                                date = datetime.strptime(date_str, "%Y-%m-%d %H:%M").date()
                            except ValueError:
                                # Fallback if no time is provided
                                date = datetime.strptime(date_str, "%Y-%m-%d").date()

                            fajr_time = datetime.strptime(prayer_time_entry['sobh'], "%H:%M").time()
                            dhuhr_time = datetime.strptime(prayer_time_entry['dhohr'], "%H:%M").time()
                            asr_time = datetime.strptime(prayer_time_entry['aser'], "%H:%M").time()
                            maghrib_time = datetime.strptime(prayer_time_entry['magreb'], "%H:%M").time()
                            isha_time = datetime.strptime(prayer_time_entry['isha'], "%H:%M").time()

                            sunrise_time_str = prayer_time_entry.get('sunrise')
                            sunrise_time = datetime.strptime(sunrise_time_str, "%H:%M").time() if sunrise_time_str else None

                            PrayerTime.objects.create(
                                location=address,
                                date=date,
                                fajr=fajr_time,
                                sunrise=sunrise_time,
                                dhuhr=dhuhr_time,
                                asr=asr_time,
                                maghrib=maghrib_time,
                                isha=isha_time
                            )

                            self.stdout.write(self.style.SUCCESS(f"Created PrayerTime for {city_name} on {date}."))
                        except ValueError as e:
                            self.stderr.write(self.style.ERROR(f"Date/time parsing error for {city_name} on {date_str}: {e}"))
                        except Exception as e:
                            self.stderr.write(self.style.ERROR(f"Error saving PrayerTime for {city_name} on {date_str}: {e}"))
