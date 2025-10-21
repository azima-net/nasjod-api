import os
import gzip
import json
import tempfile
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connection, transaction
from django.core import serializers
from django.apps import apps
import boto3
from botocore.exceptions import ClientError, NoCredentialsError


class Command(BaseCommand):
    help = 'Download and restore a database backup from Cloudflare R2'

    def add_arguments(self, parser):
        parser.add_argument(
            '--backup-file',
            type=str,
            help='Specific backup file to restore (e.g., app_20241217_143022.sql.gz). If not specified, uses the latest backup.',
        )
        parser.add_argument(
            '--keep-download',
            action='store_true',
            help='Keep the downloaded backup file after restore',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt (use with caution)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually downloading or restoring',
        )
        parser.add_argument(
            '--list-backups',
            action='store_true',
            help='List available backup files in R2 bucket',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(f'[{datetime.now()}] Starting database restore process...')
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

        # Initialize S3 client for R2
        try:
            s3_client = boto3.client(
                's3',
                endpoint_url=r2_endpoint,
                aws_access_key_id=r2_access_key,
                aws_secret_access_key=r2_secret_key,
                region_name='auto'
            )
        except Exception as e:
            raise CommandError(f'Failed to initialize R2 client: {e}')

        # Handle list backups option
        if options['list_backups']:
            self.list_available_backups(s3_client, r2_bucket)
            return

        # Determine which backup file to restore
        backup_file = options['backup_file']
        if not backup_file:
            backup_file = self.get_latest_backup(s3_client, r2_bucket)
            if not backup_file:
                raise CommandError('No backup files found in R2 bucket')

        self.stdout.write(
            self.style.SUCCESS(f'[{datetime.now()}] Using backup file: {backup_file}')
        )

        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No actual download or restore will be performed')
            )
            self.stdout.write(f'Database: {db_name}')
            self.stdout.write(f'User: {db_user}')
            self.stdout.write(f'Host: {db_host}')
            self.stdout.write(f'Port: {db_port}')
            self.stdout.write(f'Backup file: {backup_file}')
            self.stdout.write(f'R2 Bucket: {r2_bucket}')
            return

        # Confirmation prompt (unless --force is used)
        if not options['force']:
            self.stdout.write(
                self.style.WARNING(
                    f'WARNING: This will restore the database "{db_name}" from backup "{backup_file}". '
                    'This operation will REPLACE all existing data in the database.'
                )
            )
            confirm = input('Are you sure you want to continue? (yes/no): ')
            if confirm.lower() not in ['yes', 'y']:
                self.stdout.write(self.style.ERROR('Restore operation cancelled.'))
                return

        try:
            # Create temporary directory for backup
            with tempfile.TemporaryDirectory() as temp_dir:
                download_path = os.path.join(temp_dir, backup_file)

                # Step 1: Download backup from R2
                self.stdout.write(
                    self.style.SUCCESS(f'[{datetime.now()}] Downloading backup from R2...')
                )
                
                try:
                    s3_client.download_file(r2_bucket, backup_file, download_path)
                    self.stdout.write(
                        self.style.SUCCESS(f'[{datetime.now()}] Downloaded {backup_file}')
                    )
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    if error_code == 'NoSuchKey':
                        raise CommandError(f'Backup file "{backup_file}" not found in R2 bucket')
                    elif error_code == 'NoSuchBucket':
                        raise CommandError(f'R2 bucket "{r2_bucket}" does not exist')
                    else:
                        raise CommandError(f'Failed to download backup: {e}')

                # Step 2: Restore database using Django deserializers
                self.stdout.write(
                    self.style.SUCCESS(f'[{datetime.now()}] Restoring database using Django deserializers...')
                )

                # Decompress the backup file
                decompressed_path = download_path.replace('.gz', '')
                with gzip.open(download_path, 'rt', encoding='utf-8') as gz_file:
                    with open(decompressed_path, 'w', encoding='utf-8') as decompressed_file:
                        decompressed_file.write(gz_file.read())

                # Load the backup data
                with open(decompressed_path, 'r', encoding='utf-8') as backup_file:
                    backup_data = json.load(backup_file)

                # Display backup metadata
                metadata = backup_data.get('metadata', {})
                self.stdout.write(f'  Backup created: {metadata.get("created_at", "Unknown")}')
                self.stdout.write(f'  Total models: {metadata.get("total_models", 0)}')
                self.stdout.write(f'  Total objects: {metadata.get("total_objects", 0)}')

                # Restore data using transactions for safety
                with transaction.atomic():
                    restored_count = 0
                    failed_count = 0
                    
                    for model_data in backup_data.get('data', []):
                        model_name = model_data.get('model')
                        objects_data = model_data.get('data', [])
                        count = model_data.get('count', 0)
                        
                        if count > 0:
                            self.stdout.write(f'  Restoring {model_name}: {count} objects')
                            
                            try:
                                # Deserialize the objects
                                deserialized_objects = serializers.deserialize('json', json.dumps(objects_data))
                                
                                for obj in deserialized_objects:
                                    try:
                                        obj.save()
                                        restored_count += 1
                                    except Exception as e:
                                        self.stdout.write(
                                            self.style.WARNING(f'    Warning: Could not restore object: {e}')
                                        )
                                        failed_count += 1
                                        
                            except Exception as e:
                                self.stdout.write(
                                    self.style.WARNING(f'  Warning: Could not restore {model_name}: {e}')
                                )
                                failed_count += count

                self.stdout.write(
                    self.style.SUCCESS(f'  Restored {restored_count} objects successfully')
                )
                if failed_count > 0:
                    self.stdout.write(
                        self.style.WARNING(f'  Failed to restore {failed_count} objects')
                    )

                self.stdout.write(
                    self.style.SUCCESS(f'[{datetime.now()}] Database restore completed successfully!')
                )

                # Optionally keep the downloaded file
                if options['keep_download']:
                    # Copy to a permanent location
                    permanent_path = f'./backup/{backup_file}'
                    os.makedirs(os.path.dirname(permanent_path), exist_ok=True)
                    import shutil
                    shutil.copy2(download_path, permanent_path)
                    self.stdout.write(
                        self.style.SUCCESS(f'Backup file saved to: {permanent_path}')
                    )

        except Exception as e:
            raise CommandError(f'Unexpected error: {e}')

    def get_latest_backup(self, s3_client, bucket_name):
        """Get the latest backup file from R2 bucket"""
        try:
            response = s3_client.list_objects_v2(Bucket=bucket_name)
            
            if 'Contents' not in response:
                return None

            # Filter for .json.gz files and sort by last modified date
            backup_files = [
                obj for obj in response['Contents']
                if obj['Key'].endswith('.json.gz')
            ]
            
            if not backup_files:
                return None

            # Sort by last modified date (newest first)
            latest_backup = max(backup_files, key=lambda x: x['LastModified'])
            return latest_backup['Key']

        except ClientError as e:
            raise CommandError(f'Failed to list backup files: {e}')

    def list_available_backups(self, s3_client, bucket_name):
        """List all available backup files in the R2 bucket"""
        try:
            response = s3_client.list_objects_v2(Bucket=bucket_name)
            
            if 'Contents' not in response:
                self.stdout.write('No backup files found in R2 bucket.')
                return

            # Filter for .json.gz files and sort by last modified date
            backup_files = [
                obj for obj in response['Contents']
                if obj['Key'].endswith('.json.gz')
            ]
            
            if not backup_files:
                self.stdout.write('No backup files found in R2 bucket.')
                return

            # Sort by last modified date (newest first)
            backup_files.sort(key=lambda x: x['LastModified'], reverse=True)

            self.stdout.write(
                self.style.SUCCESS(f'Available backup files in bucket "{bucket_name}":')
            )
            self.stdout.write('-' * 80)
            
            for i, backup in enumerate(backup_files, 1):
                size_mb = backup['Size'] / (1024 * 1024)
                self.stdout.write(
                    f'{i:2d}. {backup["Key"]:<50} '
                    f'({size_mb:.1f} MB, {backup["LastModified"].strftime("%Y-%m-%d %H:%M:%S")})'
                )

        except ClientError as e:
            raise CommandError(f'Failed to list backup files: {e}')
