# management/commands/import_products.py
from django.core.management.base import BaseCommand
import pandas as pd
import random
from management_app.models import ProductModel, Inventory
import math,re
from django.db.models.signals import post_save
from management_app.signals import handle_product_post_save


def clean_product_name(name):
    """Remove trailing numbers like '96 7' from product names."""
    return re.sub(r'\s+\d+\s+\d+$', '', str(name).strip())



class Command(BaseCommand):
    help = "Import products and update inventory from Excel"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            help="Path to the Excel file",
            required=True
        )

    def handle(self, *args, **kwargs):
        file_path = kwargs["file"]
        df = pd.read_excel(file_path)
        post_save.disconnect(handle_product_post_save, sender=ProductModel)

        for _, row in df.iterrows():
            code = str(row.get("Code") or "").strip()
            raw_name = str(row.get("Name") or "").strip()
            name = clean_product_name(raw_name)   # ✅ CLEANED NAME
            
            if "XXXXX" in name:
                continue
            
            # print(f"Original: {raw_name} | Cleaned: {name}")
            
            cur_qty = row.get("Cur Qty") or 0
            if isinstance(cur_qty, float) and math.isnan(cur_qty):
                cur_qty = 0

            # Before creating/updating product
            srate = row.get("SRate(Master)") or 0
            prate = row.get("PRate(Master)") or 0

            # Make sure NaN becomes 0
            if isinstance(srate, float) and math.isnan(srate):
                srate = 0
            if isinstance(prate, float) and math.isnan(prate):
                prate = 0

            short_desc = str(random.randint(0, 50))

            if not code or not name:
                continue  # skip empty rows

            # --- Safe get or create using unique field (item_code) ---
            product = ProductModel.objects.filter(name__iexact=name).first()
            if product and product.item_code != code:
                self.stdout.write(self.style.WARNING(
                    f"Conflict: Product with name '{name}' exists with different code '{product.item_code}'. Skipping code update to '{code}'."
                ))
                product.item_code = code
                product.save()
            
            if product and product.company_id not in [1] and name.lower() not in ["gst", "transportation"]:
                self.stdout.write(self.style.WARNING(
                    f"Conflict: Product '{name}' has unexpected company_id '{product.company_id}'. Skipping."
                ))
                product.company_id = 1
                product.save()
            
            if product and product.purchase_price != prate:
                self.stdout.write(self.style.WARNING(
                    f"Updating purchase price for '{name}' from '{product.purchase_price}' to '{prate}'."
                ))
                product.purchase_price = prate
                product.save()
            
            if not product:
                # Create new product
                print(f"Creating new product: {name}")
                product = ProductModel.objects.create(
                    item_code=code,
                    name=name,
                    product_price=srate,
                    retailer_price=srate,
                    distributer_price=srate,
                    purchase_price=prate,
                    short_name="",
                    unit="pcs",
                    description="",
                    product_use_type="Consumable",
                    product_type="Single Product",
                    is_published=False,
                    short_description=short_desc
                )
                self.stdout.write(self.style.SUCCESS(f"Created Product: {name}"))
                product.company_id = 1 # Smile nx
                # product.company_id = 3 # Star Novelty
                product.save()

            # --- Update or create inventory ---
            inventory = Inventory.objects.filter(product=product).first()
            if inventory:
                inventory.quantity = cur_qty
                inventory.save()
                self.stdout.write(self.style.SUCCESS(f"Updated Inventory for: {name}"))
            else:
                Inventory.objects.create(product=product, quantity=cur_qty)
                self.stdout.write(self.style.SUCCESS(f"Created Inventory for: {name}"))

        self.stdout.write(self.style.SUCCESS("✅ Product import completed!"))
