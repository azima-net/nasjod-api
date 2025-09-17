import json
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from django.core.files.storage import default_storage
from core.models import Address
from prayertime.models import PrayerTime
from django.db import transaction

MAX_WORKERS = 10

class Command(BaseCommand):
    help = "Fetch prayer times from block storage and store them directly into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            '--governorate-city-pairs',
            type=str,
            nargs='+',
            help='List of governorate-city pairs in format "Governorate-City" (e.g., "Gabes-Gabes Medina" "Gafsa-Gafsa")'
        )
        parser.add_argument(
            '--max-workers',
            type=int,
            default=MAX_WORKERS,
            help='Maximum number of threads for concurrent requests.'
        )

    def handle(self, *args, **options):
        governorate_city_pairs = options['governorate_city_pairs']
        max_workers = options['max_workers']
        
        if not governorate_city_pairs:
            self.stderr.write(self.style.ERROR("No governorate-city pairs provided. Use --governorate-city-pairs argument."))
            return
        
        self.stdout.write(self.style.NOTICE(f"Processing {len(governorate_city_pairs)} governorate-city pairs..."))
        
        for pair in governorate_city_pairs:
            try:
                # Split the pair into governorate and city
                if '-' not in pair:
                    self.stderr.write(self.style.ERROR(f"Invalid format for pair '{pair}'. Expected format: 'Governorate-City'"))
                    continue
                
                governorate, city = pair.split('-', 1)  # Split only on first dash
                governorate = governorate.strip()
                city = city.strip()
                
                # Create safe filename
                safe_governorate = "".join(c for c in governorate if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_city = "".join(c for c in city if c.isalnum() or c in (' ', '-', '_')).rstrip()
                filename = f"prayer-times-{safe_governorate}-{safe_city}.json"
                
                self.stdout.write(self.style.NOTICE(f"Processing {governorate} - {city}..."))
                
                # Get prayer times data from file
                prayer_times_data = self.get_file_as_dict(filename)
                
                # Store data in database
                self.store_data(prayer_times_data, governorate, city)
                
                self.stdout.write(self.style.SUCCESS(f"Successfully processed {governorate} - {city}"))
                
            except FileNotFoundError as e:
                self.stderr.write(self.style.ERROR(f"File not found for {pair}: {e}"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error processing {pair}: {e}"))
        
        self.stdout.write(self.style.SUCCESS("All governorate-city pairs have been processed."))
    
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

    def store_data(self, prayer_times_data, governorate_name, city_name):
        """
        Stores the prayer times data into the database.
        Expected format: {"prayer_times": [{"date": "...", "sobh": "...", ...}, ...]}
        """
        with transaction.atomic():
            # Create a new Address entry (without coordinates since they're not in the file)
            try:
                address = Address.objects.create(
                    city=city_name,
                    state=governorate_name,
                    country="Tunisia",
                    coordinates=None  # No coordinates in the new format
                )
                self.stdout.write(self.style.SUCCESS(f"Created new address for {city_name}, {governorate_name}."))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error creating Address for {city_name}, {governorate_name}: {e}"))
                return

            # Process prayer times
            prayer_times_list = prayer_times_data.get('prayer_times', [])
            if not prayer_times_list:
                self.stderr.write(self.style.WARNING(f"No prayer times found in data for {city_name}, {governorate_name}"))
                return

            for prayer_time_entry in prayer_times_list:
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
