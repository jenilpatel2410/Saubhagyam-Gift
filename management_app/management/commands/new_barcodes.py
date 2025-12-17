from django.core.management.base import BaseCommand
from management_app.models import ProductModel, CategoryModel
import random

class Command(BaseCommand):
    help = "Regenerate all barcode images and update company_id based on category."

    CATEGORY_COMPANY_MAP = {
        2: {58, 60},   # company_id 2 → categories 58, 60
        1: {65, 67},   # company_id 1 → categories 65, 67
        3: {70, 81},   # company_id 3 → categories 70, 81
    }

    def handle(self, *args, **options):
        products = ProductModel.objects.all()
        total = products.count()
        self.stdout.write(self.style.SUCCESS(f"Found {total} products to process."))

        for i, product in enumerate(products, start=1):
            try:
                # --- Handle category-based company assignment ---
                # category_ids = list(product.category.values_list('id', flat=True))
                # company_id = None

                # # Only apply mapping if product has exactly one category
                # if len(category_ids) == 1:
                #     cat_id = category_ids[0]
                #     for comp_id, cat_set in self.CATEGORY_COMPANY_MAP.items():
                #         if cat_id in cat_set:
                #             company_id = comp_id
                #             break

                # if company_id:
                #     product.company_id = company_id

                # --- Regenerate barcode image ---
                product.barcode_image.delete(save=False)
                product.barcode_image = None
                # product.short_description = str(random.randint(1, 50))  # Force barcode regeneration
                product.save()  # triggers barcode regeneration logic

                self.stdout.write(
                    self.style.SUCCESS(
                        f"[{i}/{total}] ✅ {product.item_code})" # updated (company={company_id or 'unchanged'})"
                    )
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"[{i}/{total}] ❌ {product.item_code}: {str(e)}")
                )
