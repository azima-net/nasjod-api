import json
from django.core.management.base import BaseCommand
from core.models import Address  # Import your Address model
import os

class Command(BaseCommand):
    help = 'Populate the Address model from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='The path to the JSON file with address data')

    def handle(self, *args, **options):
        file_path = options['file_path']

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        with open(file_path, 'r') as file:
            data = json.load(file)

        # Counter for tracking how many addresses are populated
        created_count = 0

        for entry in data:
            if entry['model'] == 'core.address':
                fields = entry.get('fields', {})

                # Extract the fields with conditions
                street = fields.get('street')
                city = fields.get('city')
                state = fields.get('state')
                country = fields.get('country')
                coordinates = fields.get('coordinates')

                # Skip records where street is "$"
                if street == "$":
                    continue

                # Create a new Address instance if all required fields are present
                if all([street, city, state, country, coordinates]):
                    Address.objects.update_or_create(
                        pk=entry['pk'],
                        defaults={
                            'street': street,
                            'city': city,
                            'state': state,
                            'country': country,
                            'coordinates': coordinates,
                        }
                    )
                    created_count += 1

        self.stdout.write(self.style.SUCCESS(f"{created_count} addresses populated successfully."))
