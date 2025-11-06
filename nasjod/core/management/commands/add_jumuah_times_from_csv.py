import csv
import re
from datetime import time, datetime
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from django.db import transaction
from django.core.exceptions import ValidationError

from masjid.models import Masjid
from prayertime.models import JumuahPrayerTime
from core._helpers import get_next_friday


class Command(BaseCommand):
    help = 'Add jumuah prayer times from CSV file by matching masjids using latitude and longitude'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='The path to the CSV file containing jumuah times')
        parser.add_argument('--dry-run', action='store_true', help='Run without actually creating objects')
        parser.add_argument('--tolerance', type=float, default=0.001, 
                          help='Coordinate matching tolerance in degrees (default: 0.001, ~100 meters)')
        parser.add_argument('--date', type=str, default=None,
                          help='Date for jumuah time in YYYY-MM-DD format (default: next Friday)')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        dry_run = options['dry_run']
        tolerance = options['tolerance']
        date_str = options.get('date')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Running in DRY RUN mode - no objects will be created'))
        
        # Determine the date for jumuah times
        if date_str:
            try:
                jumuah_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                if jumuah_date.weekday() != 4:  # 4 is Friday
                    self.stdout.write(
                        self.style.WARNING(f'Warning: {jumuah_date} is not a Friday. Jumuah times should be on Fridays.')
                    )
            except ValueError:
                self.stdout.write(self.style.ERROR(f'Invalid date format: {date_str}. Use YYYY-MM-DD'))
                return
        else:
            jumuah_date = get_next_friday()
        
        self.stdout.write(f'Using date: {jumuah_date} ({"Friday" if jumuah_date.weekday() == 4 else "NOT Friday"})')

        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                # Use semicolon as delimiter based on the CSV structure
                reader = csv.DictReader(file, delimiter=';')
                
                matched_count = 0
                created_count = 0
                updated_count = 0
                not_found_count = 0
                error_count = 0
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 because of header
                    try:
                        # Extract and validate coordinates
                        try:
                            lat = float(row.get('lat', ''))
                            lon = float(row.get('lon', ''))
                        except (ValueError, TypeError):
                            error_count += 1
                            self.stdout.write(
                                self.style.ERROR(f'Row {row_num}: Invalid coordinates (lat: {row.get("lat")}, lon: {row.get("lon")})')
                            )
                            continue
                        
                        # Get jumuah times from CSV
                        jumuah_times_str = row.get('jumuah_times', '').strip()
                        if not jumuah_times_str:
                            error_count += 1
                            self.stdout.write(
                                self.style.WARNING(f'Row {row_num}: No jumuah_times found')
                            )
                            continue
                        
                        # Parse jumuah times (can be single or multiple times separated by comma)
                        jumuah_times = self.parse_jumuah_times(jumuah_times_str)
                        if not jumuah_times:
                            error_count += 1
                            self.stdout.write(
                                self.style.ERROR(f'Row {row_num}: Could not parse jumuah_times: {jumuah_times_str}')
                            )
                            continue
                        
                        # Find matching masjid(s) by coordinates
                        masjids = self.find_masjids_by_coordinates(lat, lon, tolerance)
                        
                        if not masjids.exists():
                            not_found_count += 1
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Row {row_num}: No masjid found near coordinates ({lat}, {lon}) '
                                    f'for "{row.get("name_en", "Unknown")}"'
                                )
                            )
                            continue
                        
                        matched_count += 1
                        
                        if not dry_run:
                            # Create or update JumuahPrayerTime for each matching masjid
                            row_created = 0
                            row_updated = 0
                            for masjid in masjids:
                                for jumuah_time in jumuah_times:
                                    with transaction.atomic():
                                        jumuah_prayer_time, created = JumuahPrayerTime.objects.update_or_create(
                                            masjid=masjid,
                                            date=jumuah_date,
                                            jumuah_time=jumuah_time,
                                            defaults={
                                                'first_timeslot_jumuah': False,
                                            }
                                        )
                                        
                                        if created:
                                            created_count += 1
                                            row_created += 1
                                        else:
                                            updated_count += 1
                                            row_updated += 1
                            
                            action = "Created" if row_created > 0 else "Updated"
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'Row {row_num}: {action} jumuah times for '
                                    f'"{masjids.first().name}" ({masjids.count()} masjid(s), {len(jumuah_times)} time(s))'
                                )
                            )
                        else:
                            # Dry run mode - just report what would be done
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'Row {row_num}: Would create/update jumuah times for '
                                    f'"{row.get("name_en", "Unknown")}" '
                                    f'({masjids.count()} masjid(s), {len(jumuah_times)} time(s))'
                                )
                            )
                                
                    except Exception as e:
                        error_count += 1
                        self.stdout.write(
                            self.style.ERROR(f'Row {row_num}: Error processing "{row.get("name_en", "Unknown")}": {str(e)}')
                        )
                        if not dry_run:
                            continue

                # Summary
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('=' * 60))
                if dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Dry run completed. Would process: {matched_count} matched, '
                            f'{not_found_count} not found, {error_count} errors'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Import completed. Matched: {matched_count}, '
                            f'Created: {created_count}, Updated: {updated_count}, '
                            f'Not found: {not_found_count}, Errors: {error_count}'
                        )
                    )
                self.stdout.write(self.style.SUCCESS('=' * 60))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found: {csv_file_path}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Unexpected error: {str(e)}'))

    def find_masjids_by_coordinates(self, lat, lon, tolerance):
        """
        Find masjids with coordinates within tolerance distance.
        Uses PostGIS dwithin for efficient spatial queries.
        For geographic coordinates (SRID 4326), tolerance must be in degrees.
        """
        from django.contrib.gis.geos import Point
        
        # Create a point from the CSV coordinates
        csv_point = Point(lon, lat, srid=4326)
        
        # Find masjids with addresses within tolerance using dwithin
        # For geographic coordinates (SRID 4326), dwithin requires tolerance in degrees
        # tolerance is in degrees (0.001 degrees ≈ 111 meters)
        masjids = Masjid.objects.filter(
            address__coordinates__isnull=False,
            address__coordinates__dwithin=(csv_point, tolerance)
        ).select_related('address')
        
        return masjids

    def parse_jumuah_times(self, jumuah_times_str):
        """
        Parse jumuah times from CSV string.
        Can handle formats like:
        - "13:00"
        - "12:45"
        - "14:00, 14:00" (multiple times)
        - "12:30, 13:00" (multiple different times)
        """
        if not jumuah_times_str or not jumuah_times_str.strip():
            return []
        
        # Split by comma and process each time
        time_strings = [t.strip() for t in jumuah_times_str.split(',')]
        parsed_times = []
        
        for time_str in time_strings:
            if not time_str:
                continue
            
            # Match time format HH:MM or HH:MM:SS
            time_pattern = r'^(\d{1,2}):(\d{2})(?::(\d{2}))?$'
            time_match = re.match(time_pattern, time_str)
            
            if time_match:
                try:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2))
                    second = int(time_match.group(3)) if time_match.group(3) else 0
                    
                    # Validate time values
                    if 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59:
                        parsed_time = time(hour, minute, second)
                        # Avoid duplicates
                        if parsed_time not in parsed_times:
                            parsed_times.append(parsed_time)
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'Invalid time values: {time_str}')
                        )
                except (ValueError, TypeError) as e:
                    self.stdout.write(
                        self.style.WARNING(f'Error parsing time "{time_str}": {str(e)}')
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Time format not recognized: {time_str}')
                )
        
        return parsed_times

