import json
from django.core.management.base import BaseCommand
from masjid.models import Masjid

class Command(BaseCommand):
    help = 'Populate the Masjid model from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='The path to the JSON file containing masjid data')

    def handle(self, *args, **options):
        json_file_path = options['json_file']
        
        # Load JSON data
        with open(json_file_path, 'r', encoding='utf-8') as file:
            masjids_data = json.load(file)

        # Iterate over each masjid entry in the JSON file
        for entry in masjids_data:
            fields = entry['fields']
            
            # Remove the address key from fields
            if 'address' in fields:
                del fields['address']


            # Create or update the masjid instance
            masjid, created = Masjid.objects.update_or_create(
                pk=entry['pk'],
                defaults=fields  # Pass in fields with address set to None
            )

            # Log output
            if created:
                self.stdout.write(self.style.SUCCESS(f'Masjid "{masjid.name}" created successfully'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Masjid "{masjid.name}" updated successfully'))

        self.stdout.write(self.style.SUCCESS('All masjids processed successfully'))
