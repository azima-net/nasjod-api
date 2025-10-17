import csv
import re
import requests
import os
from datetime import time, datetime
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.files.images import ImageFile
from PIL import Image
import io

from masjid.models import Masjid
from core.models import Address
from prayertime.models import IqamaTime


class Command(BaseCommand):
    help = 'Import mosques from CSV file with prayer times'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='The path to the CSV file containing mosque data')
        parser.add_argument('--dry-run', action='store_true', help='Run without actually creating objects')
        parser.add_argument('--skip-images', action='store_true', help='Skip downloading and uploading images')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        dry_run = options['dry_run']
        skip_images = options['skip_images']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Running in DRY RUN mode - no objects will be created'))
        
        if skip_images:
            self.stdout.write(self.style.WARNING('Skipping image downloads and uploads'))

        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                # Use semicolon as delimiter based on the CSV structure
                reader = csv.DictReader(file, delimiter=';')
                
                created_count = 0
                updated_count = 0
                error_count = 0
                image_success_count = 0
                image_error_count = 0
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 because of header
                    try:
                        with transaction.atomic():
                            if not dry_run:
                                masjid, created = self.create_masjid_from_row(row, skip_images)
                                if created:
                                    created_count += 1
                                    self.stdout.write(
                                        self.style.SUCCESS(f'Row {row_num}: Created masjid "{masjid.name}"')
                                    )
                                else:
                                    updated_count += 1
                                    self.stdout.write(
                                        self.style.SUCCESS(f'Row {row_num}: Updated masjid "{masjid.name}"')
                                    )
                                
                                # Handle image download and upload
                                if not skip_images and row.get('image1'):
                                    try:
                                        image_uploaded = self.download_and_upload_image(row['image1'], masjid)
                                        if image_uploaded:
                                            image_success_count += 1
                                            self.stdout.write(
                                                self.style.SUCCESS(f'Row {row_num}: Image uploaded for "{masjid.name}"')
                                            )
                                        else:
                                            image_error_count += 1
                                            self.stdout.write(
                                                self.style.WARNING(f'Row {row_num}: Failed to upload image for "{masjid.name}"')
                                            )
                                    except Exception as e:
                                        image_error_count += 1
                                        self.stdout.write(
                                            self.style.WARNING(f'Row {row_num}: Image error for "{masjid.name}": {str(e)}')
                                        )
                            else:
                                # In dry run mode, just validate the data
                                self.validate_row_data(row)
                                self.stdout.write(
                                    self.style.SUCCESS(f'Row {row_num}: Valid data for "{row.get("name_en", "Unknown")}"')
                                )
                                
                    except Exception as e:
                        error_count += 1
                        self.stdout.write(
                            self.style.ERROR(f'Row {row_num}: Error processing "{row.get("name_en", "Unknown")}": {str(e)}')
                        )
                        if not dry_run:
                            continue

                # Summary
                if dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(f'Dry run completed. {created_count + updated_count} records would be processed, {error_count} errors found.')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'Import completed. Created: {created_count}, Updated: {updated_count}, Errors: {error_count}')
                    )
                    if not skip_images:
                        self.stdout.write(
                            self.style.SUCCESS(f'Images: {image_success_count} uploaded, {image_error_count} failed')
                        )

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found: {csv_file_path}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Unexpected error: {str(e)}'))

    def validate_row_data(self, row):
        """Validate row data without creating objects (for dry run)"""
        # Check required fields
        required_fields = ['name_en', 'governorate', 'lat', 'lon']
        for field in required_fields:
            if not row.get(field):
                raise ValidationError(f'Missing required field: {field}')
        
        # Validate coordinates
        try:
            float(row['lat'])
            float(row['lon'])
        except (ValueError, TypeError):
            raise ValidationError('Invalid coordinates')

    def create_masjid_from_row(self, row, skip_images=False):
        """Create or update a masjid from CSV row data"""
        
        # Extract and validate coordinates
        try:
            lat = float(row['lat'])
            lon = float(row['lon'])
            coordinates = Point(lon, lat)  # Note: Point takes (x, y) which is (lon, lat)
        except (ValueError, TypeError):
            raise ValidationError('Invalid coordinates in CSV row')

        # Create or get address
        address, address_created = Address.objects.get_or_create(
            coordinates=coordinates,
            defaults={
                'country': 'tunisia',
                'city': row.get('governorate', '').strip(),
                'zip_code': row.get('zipcode', '').strip() or None,
                'additional_info': row.get('address_mawaqit', '').strip() or None,
            }
        )

        # Create or update masjid
        masjid_data = {
            'name': row.get('name_en', '').strip(),
            'name_ar': row.get('name_ar', '').strip() or None,
            'telephone': row.get('phone', '').strip() or None,
            'address': address,
        }
        
        # Only add cover if we're not handling images separately
        if skip_images:
            masjid_data['cover'] = row.get('image1', '').strip() or None

        # Remove None values to avoid overwriting existing data
        masjid_data = {k: v for k, v in masjid_data.items() if v is not None}

        masjid, created = Masjid.objects.update_or_create(
            name=masjid_data['name'],
            address=address,
            defaults=masjid_data
        )

        # Create or update IqamaTime
        self.create_iqama_time(masjid, row)

        return masjid, created

    def create_iqama_time(self, masjid, row):
        """Create or update IqamaTime for the masjid"""
        
        # Parse fajr_iqama
        fajr_iqama = self.parse_iqama_value(row.get('fajr_iqama', ''))
        
        # Parse dhuhr_iqama with special logic
        dhuhr_data = self.parse_dhuhr_iqama(row.get('dhuhr_iqama', ''))
        
        # Parse other iqama times
        asr_iqama = self.parse_iqama_value(row.get('asr_iqama', ''))
        maghrib_iqama = self.parse_iqama_value(row.get('maghrib_iqama', ''))
        isha_iqama = self.parse_iqama_value(row.get('isha_iqama', ''))

        # Prepare iqama data
        iqama_data = {
            'fajr_iqama': fajr_iqama,
            'asr_iqama': asr_iqama,
            'maghrib_iqama': maghrib_iqama,
            'isha_iqama': isha_iqama,
        }

        # Add dhuhr-related fields based on parsing result
        if dhuhr_data['type'] == 'positive_int':
            iqama_data['dhuhr_iqama'] = dhuhr_data['value']
        elif dhuhr_data['type'] == 'negative_int':
            iqama_data['dhuhr_iqama_from_asr'] = abs(dhuhr_data['value'])
        elif dhuhr_data['type'] == 'time':
            iqama_data['dhuhr_iqama_hour'] = dhuhr_data['value']

        # Remove None values
        iqama_data = {k: v for k, v in iqama_data.items() if v is not None}

        # Create or update IqamaTime (using today's date as default)
        from django.utils import timezone
        today = timezone.now().date()
        
        iqama_time, iqama_created = IqamaTime.objects.update_or_create(
            masjid=masjid,
            date=today,
            defaults=iqama_data
        )

        return iqama_time, iqama_created

    def parse_iqama_value(self, value):
        """Parse iqama value from CSV string"""
        if not value or value.strip() == '':
            return None
        
        value = value.strip()
        
        # Handle positive/negative integers
        if value.startswith('+') or value.startswith('-'):
            try:
                return int(value)
            except ValueError:
                return None
        
        # Handle plain integers
        try:
            return int(value)
        except ValueError:
            return None

    def parse_dhuhr_iqama(self, value):
        """Parse dhuhr iqama with special logic for different formats"""
        if not value or value.strip() == '':
            return {'type': None, 'value': None}
        
        value = value.strip()
        
        # Check if it's a time format (HH:MM or HH:MM:SS)
        time_pattern = r'^(\d{1,2}):(\d{2})(?::(\d{2}))?$'
        time_match = re.match(time_pattern, value)
        
        if time_match:
            try:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                second = int(time_match.group(3)) if time_match.group(3) else 0
                
                # Validate time values
                if 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59:
                    return {'type': 'time', 'value': time(hour, minute, second)}
            except (ValueError, TypeError):
                pass
        
        # Handle positive/negative integers
        if value.startswith('+') or value.startswith('-'):
            try:
                int_value = int(value)
                if int_value > 0:
                    return {'type': 'positive_int', 'value': int_value}
                else:
                    return {'type': 'negative_int', 'value': int_value}
            except ValueError:
                pass
        
        # Handle plain integers
        try:
            int_value = int(value)
            if int_value > 0:
                return {'type': 'positive_int', 'value': int_value}
            else:
                return {'type': 'negative_int', 'value': int_value}
        except ValueError:
            pass
        
        # If we can't parse it, return None
        return {'type': None, 'value': None}

    def download_and_upload_image(self, image_url, masjid):
        """Download image from URL and upload to S3"""
        if not image_url or not image_url.strip():
            return False
        
        try:
            # Download the image
            response = requests.get(image_url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Check if it's actually an image
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                self.stdout.write(
                    self.style.WARNING(f'URL does not point to an image: {image_url}')
                )
                return False
            
            # Read the image data
            image_data = response.content
            
            # Validate and process the image with PIL
            try:
                image = Image.open(io.BytesIO(image_data))
                # Convert to RGB if necessary (handles RGBA, P mode, etc.)
                if image.mode in ('RGBA', 'P'):
                    image = image.convert('RGB')
                
                # Save to BytesIO buffer
                output = io.BytesIO()
                image.save(output, format='JPEG', quality=85, optimize=True)
                image_data = output.getvalue()
                output.close()
                
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Error processing image: {str(e)}')
                )
                return False
            
            # Generate filename using the image_path_upload helper
            from core._helpers import image_path_upload
            filename = image_path_upload(masjid, f'mosque_cover_{masjid.id}.jpg')
            
            # Upload to S3 using Django's default storage
            content_file = ContentFile(image_data, name=filename)
            uploaded_path = default_storage.save(filename, content_file)
            
            # Update the masjid with the uploaded image path
            masjid.cover = uploaded_path
            masjid.save(update_fields=['cover'])
            
            return True
            
        except requests.RequestException as e:
            self.stdout.write(
                self.style.WARNING(f'Failed to download image from {image_url}: {str(e)}')
            )
            return False
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Unexpected error uploading image: {str(e)}')
            )
            return False
