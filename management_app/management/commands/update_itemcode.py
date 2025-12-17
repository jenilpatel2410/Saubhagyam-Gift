from django.core.management.base import BaseCommand
from management_app.models import ProductModel
import pandas as pd
from fuzzywuzzy import process


class Command(BaseCommand):
    help = "Update ProductModel.itemcode based on Excel file (Name–Code mapping)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Path to Excel file containing Name and Code columns'
        )
        parser.add_argument(
            '--threshold',
            type=int,
            default=90,
            help='Minimum match score (0–100) to consider as valid match'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        threshold = options['threshold']

        # Load Excel data
        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error reading Excel file: {e}"))
            return

        # Ensure required columns exist
        if not {'Name', 'Code'}.issubset(df.columns):
            self.stderr.write(self.style.ERROR("Excel must have 'Name' and 'Code' columns"))
            return

        excel_data = dict(zip(df['Name'].astype(str).str.strip(), df['Code'].astype(str).str.strip()))

        product_names = list(ProductModel.objects.values_list('name', flat=True))
        updated_count = 0
        skipped_count = 0

        self.stdout.write(self.style.NOTICE("Starting itemcode update...\n"))

        for excel_name, excel_code in excel_data.items():
            best_match, score = process.extractOne(excel_name, product_names)

            if score >= threshold:
                try:
                    product = ProductModel.objects.get(name=best_match)
                    product.item_code = excel_code
                    product.save(update_fields=['item_code'])
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f"✔ Updated: {best_match} → {excel_code} (score: {score})"))
                except ProductModel.DoesNotExist:
                    skipped_count += 1
                    self.stderr.write(self.style.WARNING(f"⚠ Product not found: {best_match}"))
            else:
                skipped_count += 1
                self.stderr.write(self.style.WARNING(f"❌ Low match ({score}) for Excel name: {excel_name}"))

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Done. Updated {updated_count} products. Skipped {skipped_count}."
        ))
