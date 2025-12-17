import random
from django.core.management.base import BaseCommand
from management_app.models import ProductModel, HomeCategoryModel, CategoryModel  # adjust if your subcategory model is different

class Command(BaseCommand):
    help = "Assign 5 HomeCategories uniquely to the latest 6 products of given subcategory IDs."

    def add_arguments(self, parser):
        parser.add_argument(
            '--subcat_ids',
            nargs='+',
            type=int,
            help='List of subcategory IDs to process (e.g. --subcat_ids 63 62 76)'
        )

    def handle(self, *args, **options):
        subcat_ids = options['subcat_ids'] or [63, 62, 76, 68, 80, 82]  # default list
        home_cats = list(HomeCategoryModel.objects.all().order_by('id'))

        if not home_cats:
            self.stdout.write(self.style.WARNING("⚠️ No HomeCategoryModel objects found."))
            return

        num_home_cats = len(home_cats)

        touched_products = 0

        for sc_id in subcat_ids:
            # fetch latest 6 products of this subcategory
            products = (
                ProductModel.objects.filter(sub_category__id=sc_id)
                .order_by('-created_at')[:6]
            )

            if not products:
                self.stdout.write(self.style.WARNING(f"⚠️ No products found for subcategory {sc_id}"))
                continue

            # shuffle the home categories for this block
            cats_for_block = home_cats.copy()
            random.shuffle(cats_for_block)

            # If 6 products but only 5 homecats, cycle
            for idx, prod in enumerate(products):
                # clear old home_categories for these products
                prod.home_categories.clear()
                homecat = cats_for_block[idx % num_home_cats]
                prod.home_categories.add(homecat)
                touched_products += 1

            self.stdout.write(self.style.SUCCESS(
                f"✅ Assigned home categories to {len(products)} latest products of subcategory {sc_id}"
            ))

        self.stdout.write(self.style.SUCCESS(
            f"🎯 Done! Assigned HomeCategories to {touched_products} products in total."
        ))
