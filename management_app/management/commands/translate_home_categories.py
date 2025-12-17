from googletrans import Translator
from django.core.management.base import BaseCommand
from management_app.models import HomeCategoryModel, HomeCategoryTranslation

class Command(BaseCommand):
    help = "Create translation records for existing home categories in multiple languages"

    # Languages to translate into
    LANGUAGES = ['hi', 'mr', 'gu', 'bn', 'ta', 'te', 'kn', 'ml', 'pa']

    def handle(self, *args, **kwargs):
        translator = Translator()
        created_count = 0

        for home_category in HomeCategoryModel.objects.all():
            for lang in self.LANGUAGES:
                if not HomeCategoryTranslation.objects.filter(
                    home_category=home_category,
                    language_code=lang
                ).exists():
                    try:
                        translated = translator.translate(home_category.name, src='en', dest=lang)
                        HomeCategoryTranslation.objects.create(
                            home_category=home_category,
                            language_code=lang,
                            name=translated.text,
                        )
                        created_count += 1
                        self.stdout.write(
                            f"✅ Created translation for '{home_category.name}' "
                            f"in language '{lang}' -> '{translated.text}'"
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(
                                f"⚠️ Failed to translate '{home_category.name}' in '{lang}': {e}"
                            )
                        )

        self.stdout.write(
            self.style.SUCCESS(f"🎉 Finished! {created_count} translation records created.")
        )
