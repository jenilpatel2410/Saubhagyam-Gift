# your_app/management/commands/fix_prices.py
from django.core.management.base import BaseCommand
from django.db import transaction
from management_app.models import ProductModel  # change to your actual model

class Command(BaseCommand):
    help = "Fix wrong product, retailer, and distributor prices in the database"

    def handle(self, *args, **kwargs):
        with transaction.atomic():
            products = ProductModel.objects.all()
            if not products.exists():
                self.stdout.write(self.style.WARNING("⚠️ No products found in database."))
                return

            for product in products:
                # Backup wrong values
                wrong_product_price = product.product_price     # actually retailer price
                wrong_retailer_price = product.retailer_price   # actually distributor price

                # Reassign to correct fields
                product.retailer_price = wrong_product_price
                product.distributer_price = wrong_retailer_price
                # product_price (MRP) left as is or fix manually if you have data

                product.save(update_fields=["retailer_price", "distributer_price"])

            self.stdout.write(self.style.SUCCESS(f"✅ Fixed prices for {products.count()} products."))
