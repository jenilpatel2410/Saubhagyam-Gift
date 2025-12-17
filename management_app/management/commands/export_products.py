# myapp/management/commands/export_products_excel.py
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.timezone import now
from openpyxl import Workbook
from management_app.models import ProductModel  # update with your app name



SITE_DOMAIN = "https://gift.saubhagyam.com"  # prefix for full URLs


class Command(BaseCommand):
    help = "Export products to Excel with full image and barcode URLs"

    def handle(self, *args, **options):
        filename = f"products_export_{now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = settings.BASE_DIR / filename

        wb = Workbook()
        ws = wb.active
        ws.title = "Products"

        # Header row
        headers = [
            "Image URL",
            "Product Code",
            "Name",
            "Category",
            "Sub Category",
            "Product Price (+25%)",
            "Retailer Price (+25%)",
            "Barcode Image URL",
        ]
        ws.append(headers)

        for product in ProductModel.objects.all().prefetch_related("category", "sub_category", "images"):
            # First product image (is_primary first else first one)
            first_image_obj = product.images.filter(is_primary=True).first() or product.images.first()
            first_image_url = (
                SITE_DOMAIN + first_image_obj.image.url
                if first_image_obj and first_image_obj.image
                else ""
            )

            # Barcode image URL
            barcode_image_url = (
                SITE_DOMAIN + product.barcode_image.url
                if product.barcode_image
                else ""
            )

            # Category & Subcategory
            categories = ", ".join([c.name for c in product.category.all()])
            subcategories = ", ".join([sc.name for sc in product.sub_category.all()])

            # Prices (+25%)
            product_price_with_margin = product.product_price + (Decimal("0.25") * product.product_price)
            retailer_price_with_margin = (
                product.retailer_price + (Decimal("0.25") * product.retailer_price)
                if product.retailer_price is not None
                else None
            )

            # Write row
            ws.append([
                first_image_url,
                product.item_code,
                product.name,
                categories,
                subcategories,
                float(product_price_with_margin),
                float(retailer_price_with_margin) if retailer_price_with_margin else "",
                barcode_image_url,
            ])

        wb.save(filepath)
        self.stdout.write(self.style.SUCCESS(f"Export completed: {filepath}"))
