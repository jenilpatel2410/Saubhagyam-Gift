import random
from django.core.management.base import BaseCommand
from management_app.models import Inventory, ProductModel

class Command(BaseCommand):
    help = "Create inventory records for all products (if missing) with random quantity."

    def handle(self, *args, **kwargs):
        choices = [5, 10, 20, 34, 50, 15, 9]
        products = ProductModel.objects.all()
        count = 0

        for product in products:
            inventory, created = Inventory.objects.get_or_create(
                product=product,
                defaults={"quantity": random.choice(choices)}
            )
            if not created:
                inventory.quantity += random.choice(choices)
                inventory.save(update_fields=["quantity"])
            count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Inventory initialized/updated for {count} products."))
