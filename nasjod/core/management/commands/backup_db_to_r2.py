import os
import gzip
import json
import tempfile
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connection
from django.core import serializers
from django.apps import apps
import boto3
from botocore.exceptions import ClientError, NoCredentialsError


class Command(BaseCommand):
    help = 'Create a database backup and upload it to Cloudflare R2'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep-local',
            action='store_true',
            help='Keep the local backup file after successful upload',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually creating backup or uploading',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(f'[{datetime.now()}] Starting database backup process...')
        )

        # Get configuration from Django settings and environment variables
        db_config = settings.DATABASES['default']
        db_name = db_config['NAME']
        db_user = db_config['USER']
        db_host = db_config['HOST']
        db_port = db_config.get('PORT', '5432')
        
        r2_bucket = os.getenv('R2_BACKUP_BUCKET_NAME')
        r2_endpoint = os.getenv('R2_ENDPOINT_URL')
        r2_access_key = os.getenv('R2_ACCESS_KEY_ID')
        r2_secret_key = os.getenv('R2_SECRET_ACCESS_KEY')

        # Validate required environment variables
        required_vars = {
            'R2_BACKUP_BUCKET_NAME': r2_bucket,
            'R2_ENDPOINT_URL': r2_endpoint,
            'R2_ACCESS_KEY_ID': r2_access_key,
            'R2_SECRET_ACCESS_KEY': r2_secret_key,
        }

        missing_vars = [var for var, value in required_vars.items() if not value]
        if missing_vars:
            raise CommandError(
                f'Missing required environment variables: {", ".join(missing_vars)}'
            )

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'{db_name}_{timestamp}.json'
        compressed_filename = f'{backup_filename}.gz'

        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No actual backup or upload will be performed')
            )
            self.stdout.write(f'Database: {db_name}')
            self.stdout.write(f'User: {db_user}')
            self.stdout.write(f'Host: {db_host}')
            self.stdout.write(f'Port: {db_port}')
            self.stdout.write(f'Backup file: {backup_filename}')
            self.stdout.write(f'Compressed file: {compressed_filename}')
            self.stdout.write(f'R2 Bucket: {r2_bucket}')
            self.stdout.write(f'R2 Endpoint: {r2_endpoint}')
            return

        try:
            # Create temporary directory for backup
            with tempfile.TemporaryDirectory() as temp_dir:
                backup_path = os.path.join(temp_dir, backup_filename)
                compressed_path = os.path.join(temp_dir, compressed_filename)

                # Step 1: Create database backup using Django serializers
                self.stdout.write(
                    self.style.SUCCESS(
                        f'[{datetime.now()}] Creating backup for database "{db_name}" using Django serializers...'
                    )
                )
                
                # Get all models from all apps
                all_models = []
                for app_config in apps.get_app_configs():
                    all_models.extend(app_config.get_models())
                
                # Serialize all data
                serialized_data = []
                total_objects = 0
                
                for model in all_models:
                    try:
                        # Skip proxy models and models without database tables
                        if model._meta.proxy or not model._meta.db_table:
                            continue
                            
                        # Get all objects from this model
                        objects = model.objects.all()
                        count = objects.count()
                        
                        if count > 0:
                            self.stdout.write(f'  Serializing {model._meta.label}: {count} objects')
                            
                            # Serialize the objects
                            model_data = serializers.serialize('json', objects, use_natural_foreign_keys=True, use_natural_primary_keys=True)
                            serialized_data.append({
                                'model': model._meta.label,
                                'count': count,
                                'data': json.loads(model_data)
                            })
                            total_objects += count
                            
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f'  Warning: Could not serialize {model._meta.label}: {e}')
                        )
                        continue
                
                # Create the backup structure
                backup_data = {
                    'metadata': {
                        'created_at': datetime.now().isoformat(),
                        'django_version': settings.DATABASES['default']['NAME'],
                        'total_models': len(serialized_data),
                        'total_objects': total_objects,
                    },
                    'data': serialized_data
                }
                
                # Write the backup to file
                with open(backup_path, 'w', encoding='utf-8') as backup_file:
                    json.dump(backup_data, backup_file, indent=2, ensure_ascii=False)
                
                self.stdout.write(
                    self.style.SUCCESS(f'  Serialized {total_objects} objects from {len(serialized_data)} models')
                )

                # Step 2: Compress the backup
                self.stdout.write(
                    self.style.SUCCESS(f'[{datetime.now()}] Compressing backup...')
                )
                
                with open(backup_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        f_out.writelines(f_in)

                # Step 3: Upload to R2
                self.stdout.write(
                    self.style.SUCCESS(
                        f'[{datetime.now()}] Uploading backup to Cloudflare R2 bucket "{r2_bucket}"...'
                    )
                )

                # Initialize S3 client for R2
                s3_client = boto3.client(
                    's3',
                    endpoint_url=r2_endpoint,
                    aws_access_key_id=r2_access_key,
                    aws_secret_access_key=r2_secret_key,
                    region_name='auto'  # R2 uses 'auto' as region
                )

                # Upload the compressed backup
                try:
                    s3_client.upload_file(
                        compressed_path,
                        r2_bucket,
                        compressed_filename
                    )
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'[{datetime.now()}] Backup successfully uploaded to '
                            f'{r2_endpoint}/{r2_bucket}/{compressed_filename}'
                        )
                    )

                    # Optionally remove local backup file
                    if not options['keep_local']:
                        self.stdout.write(
                            self.style.SUCCESS(f'[{datetime.now()}] Local backup file removed.')
                        )

                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    if error_code == 'NoSuchBucket':
                        raise CommandError(f'R2 bucket "{r2_bucket}" does not exist')
                    elif error_code == 'AccessDenied':
                        raise CommandError(f'Access denied to R2 bucket "{r2_bucket}"')
                    else:
                        raise CommandError(f'R2 upload failed: {e}')
                except NoCredentialsError:
                    raise CommandError('R2 credentials not found or invalid')

        except Exception as e:
            raise CommandError(f'Unexpected error: {e}')

        self.stdout.write(
            self.style.SUCCESS(f'[{datetime.now()}] Database backup process completed successfully!')
        )
