import os
import gzip
import subprocess
import tempfile
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connection
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

                # Step 2: Restore database
                self.stdout.write(
                    self.style.SUCCESS(f'[{datetime.now()}] Restoring database...')
                )

                # Decompress and pipe to psql directly
                restore_cmd = [
                    'psql',
                    '-h', db_host,
                    '-p', str(db_port),
                    '-U', db_user,
                    '-d', db_name
                ]

                # Set PGPASSWORD environment variable for authentication
                env = os.environ.copy()
                if db_config.get('PASSWORD'):
                    env['PGPASSWORD'] = db_config['PASSWORD']

                with gzip.open(download_path, 'rt') as gz_file:
                    result = subprocess.run(
                        restore_cmd,
                        stdin=gz_file,
                        stderr=subprocess.PIPE,
                        text=True,
                        env=env
                    )

                if result.returncode != 0:
                    raise CommandError(f'Database restore failed: {result.stderr}')

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

        except subprocess.CalledProcessError as e:
            raise CommandError(f'Command failed: {e}')
        except FileNotFoundError as e:
            raise CommandError(f'Required command not found: {e}')
        except Exception as e:
            raise CommandError(f'Unexpected error: {e}')

    def get_latest_backup(self, s3_client, bucket_name):
        """Get the latest backup file from R2 bucket"""
        try:
            response = s3_client.list_objects_v2(Bucket=bucket_name)
            
            if 'Contents' not in response:
                return None

            # Filter for .sql.gz files and sort by last modified date
            backup_files = [
                obj for obj in response['Contents']
                if obj['Key'].endswith('.sql.gz')
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

            # Filter for .sql.gz files and sort by last modified date
            backup_files = [
                obj for obj in response['Contents']
                if obj['Key'].endswith('.sql.gz')
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
