import csv
from django.core.management.base import BaseCommand, CommandError
from user_app.models import CitiesModel, CountryModel, StatesModel


class Command(BaseCommand):
    help = "Import cities from a CSV file into CitiesModel"

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Path to the CSV file to import (with id,country,state,name,is_active columns)',
        )

    def handle(self, *args, **options):
        file_path = options['file']

        try:
            with open(file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                count = 0
                for row in reader:
                    try:
                        city_name = row['name'].strip()
                        is_active = row.get('is_active', '1') in ['1', 'True', 'true']

                        # create or update
                        obj, created = CitiesModel.objects.update_or_create(
                            country_id=row['country'],
                            state_id=row['state'],
                            name=city_name,
                            defaults={'is_active': is_active},
                        )
                        count += 1
                    except Exception as e:
                        self.stderr.write(f"Error: {str(e)}")
                self.stdout.write(self.style.SUCCESS(f"Imported {count} cities"))
        except FileNotFoundError:
            raise CommandError(f"File {file_path} does not exist")
