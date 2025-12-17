# app/management/commands/import_excel.py
import os
import requests
import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile

from management_app.models import CategoryModel, ProductModel, ProductImageModel, CompanyModel


class Command(BaseCommand):
    help = "Import all products from Excel with Treebeard categories, images, and company/item codes"

    def handle(self, *args, **kwargs):
        # File path inside media/
        file_path = os.path.join(settings.BASE_DIR, "media", "SMILE NX.xlsx")

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"❌ File not found: {file_path}"))
            return

        # Ensure main category exists
        try:
            main_category = CategoryModel.objects.get(name="SMILE NX")
        except CategoryModel.DoesNotExist:
            main_category = CategoryModel.add_root(name="SMILE NX")
            self.stdout.write(self.style.SUCCESS(f"Created root category: {main_category}"))

        # Ensure company exists (or fetch default one)
        company, _ = CompanyModel.objects.get_or_create(name="Smile NX")

        # Load Excel
        xls = pd.ExcelFile(file_path)

        # Iterate over ALL sheets
        for sheet_name in xls.sheet_names:
            self.stdout.write(self.style.SUCCESS(f"Processing sheet: {sheet_name}"))

            # Create/get subcategory
            if not main_category.get_children().filter(name=sheet_name).exists():
                sub_category = main_category.add_child(name=sheet_name)
                self.stdout.write(self.style.SUCCESS(f"Created subcategory: {sub_category}"))
            else:
                sub_category = main_category.get_children().get(name=sheet_name)

            # Read sheet
            df = pd.read_excel(file_path, sheet_name=sheet_name)

            df = df.dropna(how="all")            # remove fully empty rows
            df = df.dropna(subset=["name"])    

            # Generate item code prefix (initials from category name)
            prefix = "".join(word[0].upper() for word in sheet_name.split() if word)
            counter = 1

            for _, row in df.iterrows():
                # Generate item code e.g. "WN001"
                item_code = f"{prefix}{str(counter).zfill(3)}"
                counter += 1

                # Create product
                product = ProductModel.objects.create(
                    name=row.get("name") or "",
                    product_price=row.get("base_price") or 0,
                    retailer_price=row.get("discounted_price") or 0,
                    company=company,
                    item_code=item_code,
                )

                # Assign categories (M2M)
                product.category.add(main_category)
                product.sub_category.add(sub_category)

                # Handle product image (download from link)
                image_url = row.get("image_link")
                if image_url and isinstance(image_url, str):
                    try:
                        response = requests.get(image_url, timeout=10)
                        if response.status_code == 200:
                            file_name = os.path.basename(image_url.split("?")[0])
                            image_content = ContentFile(response.content, name=file_name)
                            ProductImageModel.objects.create(product=product, image=image_content)
                            self.stdout.write(self.style.SUCCESS(f"🖼️ Added image for: {product.name}"))
                        else:
                            self.stdout.write(self.style.WARNING(f"⚠️ Failed to download image: {image_url}"))
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"⚠️ Error downloading {image_url}: {e}"))

                self.stdout.write(self.style.SUCCESS(f"✅ Added product: {product.name} [{item_code}]"))

        self.stdout.write(self.style.SUCCESS("🎉 Full data import completed!"))
