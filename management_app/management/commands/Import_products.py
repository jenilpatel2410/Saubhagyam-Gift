import os
import pandas as pd
import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.conf import settings
from management_app.models import (
    ProductModel, CategoryModel, ProductImageModel
)


class Command(BaseCommand):
    help = "Import products from Excel files into ProductModel with prefix item codes and image download"

    def add_arguments(self, parser):
        parser.add_argument(
            '--folder',
            type=str,
            default=os.path.join(settings.BASE_DIR, "import_excels"),
            help="Folder path containing Excel files"
        )

    def generate_prefix(self, name):
        """Generate prefix from subcategory name (first letters of each word)."""
        return "".join(word[0].upper() for word in name.split() if word)

    def get_or_create_category_and_subcategory(self, category_name, subcategory_name):
        """
        Returns (category, subcategory) nodes.
        - category_name: top-level category
        - subcategory_name: child category
        """
        if not category_name:
            return None, None

        # Normalize strings
        category_name = category_name.strip().title()
        subcategory_name = subcategory_name.strip().title() if subcategory_name else None

        try:
            main_category = CategoryModel.objects.get(name=category_name)
        except CategoryModel.DoesNotExist:
            main_category = CategoryModel.add_root(name=category_name)
            
        if not main_category.get_children().filter(name=subcategory_name).exists():
            sub_category = main_category.add_child(name=subcategory_name)
            # self.stdout.write(self.style.SUCCESS(f"Created subcategory: {sub_category}"))
        else:
            sub_category = main_category.get_children().get(name=subcategory_name)
        
        return main_category, sub_category

    def handle(self, *args, **kwargs):
        folder = kwargs['folder']

        self.stdout.write(self.style.NOTICE(f"📂 Looking for Excel files in {folder}"))

        if not os.path.exists(folder):
            self.stdout.write(self.style.ERROR("❌ Folder does not exist"))
            return

        # Dictionary to maintain counters per prefix
        counters = {}

        def safe_value(value, default=""):
            if value is None:
                return default
            if isinstance(value, float) and pd.isna(value):
                return default
            return value

        for file_name in os.listdir(folder):
            if file_name.endswith((".xlsx", ".xls")):
                file_path = os.path.join(folder, file_name)
                self.stdout.write(self.style.SUCCESS(f"➡️ Processing {file_name}"))

                df = pd.read_excel(file_path)
                
                df = df.dropna(how="all")  
                df = df.where(pd.notnull(df), None)

                for _, row in df.iterrows():
                    try:
                        product_name = safe_value(row.get("Product Name"), None)
                        if not product_name:
                            # Skip rows without product name
                            self.stdout.write(self.style.WARNING(f"⚠️ Skipping row with empty Product Name: {row.to_dict()}"))
                            continue

                        # Get or create Category & SubCategory
                        category_name = safe_value(row.get("Category"), None)
                        subcategory_name = safe_value(row.get("SubCategory"), None)
                        
                        category, subcategory = self.get_or_create_category_and_subcategory(
                            category_name, subcategory_name
                        )

                        # Generate item code prefix from SubCategory
                        if subcategory:
                            prefix = self.generate_prefix(subcategory.name)
                        elif category:
                            prefix = self.generate_prefix(category.name)  # fallbac
                        else:
                            prefix = "GEN"

                        # Initialize counter if not used yet
                        if prefix not in counters:
                            counters[prefix] = 1

                        # Generate item code (e.g., WABGI001)
                        item_code = f"{prefix}{str(counters[prefix]).zfill(3)}"
                        counters[prefix] += 1

                        product_price = safe_value(row.get("Product Price"), 0)
                        discounted_price = safe_value(row.get("Discounted price"), 0)
        
                        # Create or get product
                        product, created = ProductModel.objects.get_or_create(
                            name=product_name,
                            defaults={
                                "short_name": safe_value(row.get("Sku"), ""),
                                "unit": "pcs",
                                "product_price": product_price,
                                "retailer_price": discounted_price,
                                "item_code": item_code,
                                "description": safe_value(row.get("Product Description"), ""),
                                "product_use_type": safe_value(row.get('Tax "type"'), "Consumable"),
                                "product_type": safe_value(row.get("Set Type"), "Single Product"),
                            }
                        )
                        
                        # Assign ManyToMany categories properly
                        if category:
                            product.category.set([category])  # or add(category) if you want to keep existing
                        if subcategory:
                            product.sub_category.set([subcategory])

                        if created:
                            # self.stdout.write(self.style.SUCCESS(f"✅ Added: {product.name} [{item_code}]"))
                            ...
                        else:
                            self.stdout.write(self.style.WARNING(f"⚠️ Exists: {product.name}"))

                        # Save product image from URL
                        image_url = safe_value(row.get("Product Picture url"), "")
                        if image_url and isinstance(image_url, str):
                            try:
                                response = requests.get(image_url, timeout=10)
                                if response.status_code == 200:
                                    file_name = os.path.basename(image_url.split("?")[0])
                                    image_content = ContentFile(response.content, name=file_name)
                                    ProductImageModel.objects.create(product=product, image=image_content)
                                    # self.stdout.write(self.style.SUCCESS(f"🖼️ Image saved for {product.name}"))
                                else:
                                    self.stdout.write(self.style.WARNING(f"⚠️ Failed to download image: {image_url}"))
                            except Exception as e:
                                self.stdout.write(self.style.WARNING(f"⚠️ Error downloading {image_url}: {e}"))

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"❌ Error on row {row.to_dict()} => {e}"))
