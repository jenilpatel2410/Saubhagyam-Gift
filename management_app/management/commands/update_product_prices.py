from django.core.management.base import BaseCommand
from django.db.models import F,Q
from management_app.models import ProductModel

class Command(BaseCommand):
    help = "Set retailer and distributer prices same as product price if they are 0 or None"

    def handle(self, *args, **kwargs):
        # Update retailer_price where it is 0 or None
        ProductModel.objects.filter(
            Q(retailer_price__in=[0, None]) & Q(distributer_price__in=[0, None])
        ).update(
            retailer_price=F('product_price'),
            distributer_price=F('product_price')
        )
        self.stdout.write(self.style.SUCCESS("Retailer and distributer prices updated successfully."))
