from django.core.management.base import BaseCommand
from googletrans import Translator
from management_app.models import ProductModel, ProductTranslation  # adjust app name if needed

class Command(BaseCommand):
    help = "Create translation records for existing products in multiple languages"

    LANGUAGES = ['hi', 'mr', 'gu', 'bn', 'ta', 'te', 'kn', 'ml', 'pa'] 

    def handle(self, *args, **kwargs):
        translator = Translator()
        created_count = 0
        skipped_count = 0
        error_count = 0

        for product in ProductModel.objects.all():
            for lang in self.LANGUAGES:
                try:
                    # Check if translation already exists
                    if ProductTranslation.objects.filter(product=product, language_code=lang).exists():
                        skipped_count += 1
                        continue  # skip this language for this product

                    # Translate product fields
                    name_translated = translator.translate(product.name or "", src='en', dest=lang).text if product.name else ""
                    short_name_translated = translator.translate(product.short_name or "", src='en', dest=lang).text if product.short_name else ""
                    feature_translated = translator.translate(product.feature or "", src='en', dest=lang).text if product.feature else ""
                    description_translated = translator.translate(product.description or "", src='en', dest=lang).text if product.description else ""

                    # Create new translation
                    ProductTranslation.objects.create(
                        product=product,
                        language_code=lang,
                        name=name_translated,
                        short_name=short_name_translated,
                        feature=feature_translated,
                        description=description_translated,
                    )
                    created_count += 1

                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f"❌ Error translating '{product.name}' in '{lang}': {str(e)}"
                        )
                    )
                    continue

        # Final summary
        self.stdout.write(
            self.style.SUCCESS(
                f"Process finished — Created: {created_count}, Skipped: {skipped_count}, Errors: {error_count}"
            )
        )