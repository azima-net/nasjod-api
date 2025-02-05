import json
import os
import requests
import json
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

# Constants
BASE_URL = "https://www.meteo.tn/horaire_gouvernorat/{date}/{state_id}/{city_id}"
BASE_URL_SUNRISE = "https://www.meteo.tn/lever_coucher_gouvernorat/{date}/{state_id}/{city_id}"
STATE_ID = 359  # Sfax state ID
CITY_IDS = [540, 538, 545, 541, 539, 536, 543, 544, 537, 542, 548, 547, 632, 546, 549]
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
            '--state-id',
            type=int,
            default=STATE_ID,
            help='State ID to fetch data for.'
        )
        parser.add_argument(
            '--city-ids',
            type=int,
            nargs='+',
            default=CITY_IDS,
            help='List of city IDs to fetch data for.'
        )
        parser.add_argument(
            '--max-workers',
            type=int,
            default=MAX_WORKERS,
            help='Maximum number of threads for concurrent requests.'
        )

    def handle(self, *args, **options):
        start_date_str = options['start_date']
        end_date_str = options['end_date']
        state_id = options['state_id']
        city_ids = options['city_ids']
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

        self.stdout.write(self.style.NOTICE(f"Fetching prayer times and sunrise from {start_date} to {end_date} for state ID {state_id}."))

        # Fetch data concurrently
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_params = {
                executor.submit(self.fetch_city_data, city_id, date_list, state_id): city_id
                for city_id in city_ids
            }

            for future in as_completed(future_to_params):
                city_id = future_to_params[future]
                try:
                    data = future.result()
                    self.stdout.write(self.style.SUCCESS(f"Successfully fetched data for city_id {city_id}."))
                    results.append(data)
                except Exception as exc:
                    self.stderr.write(self.style.ERROR(f"City_id {city_id} generated an exception: {exc}"))

        if not results:
            self.stderr.write(self.style.ERROR("No data fetched. Exiting."))
            return

        # Merge all city data
        prayer_times_data = self.merge_data(results)

        # Store data into the database
        self.store_data(prayer_times_data)

        self.stdout.write(self.style.SUCCESS("Prayer times data with sunrise has been successfully fetched and stored."))

    def fetch_city_data(self, city_id, date_list, state_id):
        """
        Fetches prayer times and sunrise data for a single city_id over the specified date range.
        Returns a nested dictionary structure:
        {
            "GovernorateName": {
                "CityName": {
                    "latitude": <lat>,
                    "longitude": <lng>,
                    "prayer_times": [ {date: <>, sobh: <>, dhohr: <>, aser: <>, magreb: <>, isha: <>, sunrise: <>}, ...]
                },
                ...
            }
        }
        """
        city_data = {}

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

                governorate_name = data_main.get("gouvernorat", {}).get("intituleAn", "Unknown")
                city_name = data_main.get("delegation", {}).get("intituleAn", "Unknown")
                lat = data_main.get("lat")
                lng = data_main.get("lng")
                sobh = data_main.get("sobh")
                dhohr = data_main.get("dhohr")
                aser = data_main.get("aser")
                magreb = data_main.get("magreb")
                isha = data_main.get("isha")
                prayer_date = data_main.get("date")

                if not all([governorate_name, city_name, lat, lng, sobh, dhohr, aser, magreb, isha, prayer_date]):
                    self.stderr.write(self.style.WARNING(f"Incomplete data for city_id {city_id} on {formatted_date}. Skipping."))
                    continue

                # Fetch sunrise data
                url_sunrise = BASE_URL_SUNRISE.format(date=formatted_date, state_id=state_id, city_id=city_id)
                response_sunrise = requests.get(url_sunrise, timeout=10)
                response_sunrise.raise_for_status()
                data_sunrise = response_sunrise.json().get("data", {})
                sunrise_time = data_sunrise.get("lever")

                # Initialize data structure
                if governorate_name not in city_data:
                    city_data[governorate_name] = {}
                if city_name not in city_data[governorate_name]:
                    city_data[governorate_name][city_name] = {
                        "latitude": lat,
                        "longitude": lng,
                        "prayer_times": []
                    }

                # Append prayer time entry including sunrise
                city_data[governorate_name][city_name]["prayer_times"].append({
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

    def merge_data(self, results_list):
        """
        Merge multiple city data dictionaries into a single dictionary.
        """
        merged = {}
        for res in results_list:
            for gov_name, gov_data in res.items():
                if gov_name not in merged:
                    merged[gov_name] = {}
                for city_name, city_info in gov_data.items():
                    if city_name not in merged[gov_name]:
                        merged[gov_name][city_name] = {
                            "latitude": city_info["latitude"],
                            "longitude": city_info["longitude"],
                            "prayer_times": []
                        }
                    # Extend the prayer times list
                    merged[gov_name][city_name]["prayer_times"].extend(city_info["prayer_times"])
        return merged

    def store_data(self, prayer_times_data):
        filename = "tunisia-sfax-prayer-times.json"
        try:
            # Convert the dictionary to JSON
            json_data = json.dumps(prayer_times_data, indent=4)

            # Save to Cloudflare R2 using Django's default storage
            file_path = os.path.join(filename)
            content = ContentFile(json_data)
            default_storage.save(file_path, content)

            self.stdout.write(f"File '{filename}' successfully uploaded to Cloudflare R2.")
        except Exception as e:
            self.stderr.write(f"An error occurred: {str(e)}")