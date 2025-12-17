from googletrans import Translator
from django.core.management.base import BaseCommand
from management_app.models import CategoryModel, CategoryTranslation

class Command(BaseCommand):
    help = "Create translation records for existing categories in multiple languages"

    LANGUAGES = ['hi', 'mr', 'gu', 'bn', 'ta', 'te', 'kn', 'ml', 'pa']

    def handle(self, *args, **kwargs):
        translator = Translator()
        created_count = 0

        for category in CategoryModel.objects.all():
            for lang in self.LANGUAGES:
                if not CategoryTranslation.objects.filter(category=category, language_code=lang).exists():
                    # Translate the category name
                    translated = translator.translate(category.name, src='en', dest=lang)
                    CategoryTranslation.objects.create(
                        category=category,
                        language_code=lang,
                        name=translated.text,
                    )
                    created_count += 1
                    self.stdout.write(
                        f"Created translation for category '{category.name}' in language '{lang}' -> '{translated.text}'"
                    )

        self.stdout.write(
            self.style.SUCCESS(f"Finished! {created_count} translation records created.")
        )

# from googletrans import Translator

# def translate_name(name):
#     LANGUAGES = ['hi', 'mr', 'gu', 'bn', 'ta', 'te', 'kn', 'ml', 'pa']  # Hindi, Marathi, Gujarati, etc.
#     translator = Translator()

#     print(f"Original name: {name}")
#     for lang in LANGUAGES:
#         translated = translator.translate(name, src='en', dest=lang)
#         print(f"{lang}: {translated.text}")

# # Example usage
# translate_name("Pathik Panchal")