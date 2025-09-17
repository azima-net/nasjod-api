import json
import os
import requests
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from django.utils import timezone
from core.models import Address
from prayertime.models import PrayerTime
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.db import transaction
from django.conf import settings

#https://www.meteo.tn/horaire_gouvernorat/2025-12-15/359/540
# Constants
BASE_URL = "https://www.meteo.tn/horaire_gouvernorat/{date}/{state_id}/{city_id}"
BASE_URL_SUNRISE = "https://www.meteo.tn/lever_coucher_gouvernorat/{date}/{state_id}/{city_id}"
DEFAULT_START_DATE = "2024-12-15"
DEFAULT_END_DATE = "2024-12-16"
MAX_WORKERS = 10

class Command(BaseCommand):
    help = "Fetch prayer times along with sunrise from API and store them directly into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-date',
            type=str,
            default=DEFAULT_START_DATE,
            help='Start date in YYYY-MM-DD format.'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            default=DEFAULT_END_DATE,
            help='End date in YYYY-MM-DD format.'
        )
        parser.add_argument(
            '--max-workers',
            type=int,
            default=MAX_WORKERS,
            help='Maximum number of threads for concurrent requests.'
        )

    def load_governorates_data(self):
        """Load governorates and delegations data from JSON file."""
        file_path = os.path.join(settings.STATIC_ROOT, 'data', 'governorats-meteo-ids.json')
        if not os.path.exists(file_path):
            # Fallback to static files directory
            file_path = os.path.join(settings.BASE_DIR, 'static', 'data', 'governorats-meteo-ids.json')
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"File not found: {file_path}"))
            return None
        except json.JSONDecodeError as e:
            self.stderr.write(self.style.ERROR(f"Invalid JSON in file: {e}"))
            return None

    def handle(self, *args, **options):
        start_date_str = options['start_date']
        end_date_str = options['end_date']
        max_workers = options['max_workers']

        # Parse dates
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError as e:
            self.stderr.write(self.style.ERROR(f"Invalid date format: {e}"))
            return

        if start_date > end_date:
            self.stderr.write(self.style.ERROR("Start date must be before or equal to end date."))
            return

        # Generate list of dates
        date_list = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

        # Load governorates data
        governorates_data = self.load_governorates_data()
        if not governorates_data:
            return

        self.stdout.write(self.style.NOTICE(f"Fetching prayer times and sunrise from {start_date} to {end_date} for all governorates."))

        # Process each governorate and its delegations
        for governorate_name, governorate_info in governorates_data.items():
            state_id = governorate_info.get('id_meteo_tunisia')
            delegations = governorate_info.get('delegations', [])
            
            if not state_id or not delegations:
                self.stderr.write(self.style.WARNING(f"Skipping {governorate_name}: missing state_id or delegations"))
                continue

            self.stdout.write(self.style.NOTICE(f"Processing {governorate_name} (state_id: {state_id}) with {len(delegations)} delegations"))

            # Process each delegation
            for delegation in delegations:
                city_id = delegation.get('id_meteo_tunisia')
                city_name = delegation.get('Name', 'Unknown')
                
                if not city_id:
                    self.stderr.write(self.style.WARNING(f"Skipping delegation {city_name}: missing city_id"))
                    continue

                try:
                    # Fetch data for this specific city
                    city_data = self.fetch_city_data(city_id, date_list, state_id)
                    
                    if city_data:
                        # Store data for this city
                        self.store_city_data(city_data, governorate_name, city_name)
                        self.stdout.write(self.style.SUCCESS(f"Successfully processed {city_name} in {governorate_name}"))
                    else:
                        self.stderr.write(self.style.WARNING(f"No data fetched for {city_name} in {governorate_name}"))
                        
                except Exception as exc:
                    self.stderr.write(self.style.ERROR(f"Error processing {city_name} in {governorate_name}: {exc}"))

        self.stdout.write(self.style.SUCCESS("All prayer times data with sunrise has been successfully fetched and stored."))

    def fetch_city_data(self, city_id, date_list, state_id):
        """
        Fetches prayer times and sunrise data for a single city_id over the specified date range.
        Returns a dictionary structure without latitude and longitude:
        {
            "prayer_times": [ {date: <>, sobh: <>, dhohr: <>, aser: <>, magreb: <>, isha: <>, sunrise: <>}, ...]
        }
        """
        city_data = {"prayer_times": []}

        for current_date in date_list:
            formatted_date = current_date.strftime("%Y-%m-%d")

            # Fetch main prayer times
            url_main = BASE_URL.format(date=formatted_date, state_id=state_id, city_id=city_id)
            try:
                response_main = requests.get(url_main, timeout=10)
                response_main.raise_for_status()
                data_main = response_main.json().get("data", {})

                if not data_main:
                    self.stderr.write(self.style.WARNING(f"No data found for city_id {city_id} on {formatted_date}."))
                    continue

                sobh = data_main.get("sobh")
                dhohr = data_main.get("dhohr")
                aser = data_main.get("aser")
                magreb = data_main.get("magreb")
                isha = data_main.get("isha")
                prayer_date = data_main.get("date")

                if not all([sobh, dhohr, aser, magreb, isha, prayer_date]):
                    self.stderr.write(self.style.WARNING(f"Incomplete data for city_id {city_id} on {formatted_date}. Skipping."))
                    continue

                # Fetch sunrise data
                url_sunrise = BASE_URL_SUNRISE.format(date=formatted_date, state_id=state_id, city_id=city_id)
                response_sunrise = requests.get(url_sunrise, timeout=10)
                response_sunrise.raise_for_status()
                data_sunrise = response_sunrise.json().get("data", {})
                sunrise_time = data_sunrise.get("lever")

                # Append prayer time entry including sunrise (without lat/lng)
                city_data["prayer_times"].append({
                    "date": prayer_date,
                    "sobh": sobh,
                    "dhohr": dhohr,
                    "aser": aser,
                    "magreb": magreb,
                    "isha": isha,
                    "sunrise": sunrise_time
                })

            except requests.RequestException as e:
                self.stderr.write(self.style.ERROR(f"Request failed for city_id {city_id} on {formatted_date}: {e}"))
            except json.JSONDecodeError:
                self.stderr.write(self.style.ERROR(f"Invalid JSON response for city_id {city_id} on {formatted_date}."))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Unexpected error for city_id {city_id} on {formatted_date}: {e}"))

        return city_data

    def store_city_data(self, city_data, governorate_name, city_name):
        """
        Store prayer times data for a specific city as a separate file.
        """
        # Create a safe filename
        safe_governorate = "".join(c for c in governorate_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_city = "".join(c for c in city_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"prayer-times-{safe_governorate}-{safe_city}.json"
        
        try:
            # Convert the dictionary to JSON
            json_data = json.dumps(city_data, indent=4, ensure_ascii=False)

            # Save to Cloudflare R2 using Django's default storage
            content = ContentFile(json_data.encode('utf-8'))
            default_storage.save(filename, content)

            self.stdout.write(f"File '{filename}' successfully uploaded to Cloudflare R2.")
        except Exception as e:
            self.stderr.write(f"An error occurred while saving {filename}: {str(e)}")