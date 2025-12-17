from googletrans import Translator
from django.core.management.base import BaseCommand
from management_app.models import PageModel, PageTranslation

class Command(BaseCommand):
    help = "Create translation records for existing pages in multiple languages"

    # Languages you want to translate to
    LANGUAGES = ['hi', 'mr', 'gu', 'bn', 'ta', 'te', 'kn', 'ml', 'pa']

    def handle(self, *args, **kwargs):
        translator = Translator()
        created_count = 0

        for page in PageModel.objects.all():
            for lang in self.LANGUAGES:
                # Skip if translation already exists
                if not PageTranslation.objects.filter(page=page, language_code=lang).exists():
                    # Translate title and description
                    try:
                        translated_title = translator.translate(page.title, src='en', dest=lang).text
                        description_text = page.description or ""
                        translated_description = translator.translate(description_text, src='en', dest=lang).text

                        PageTranslation.objects.create(
                            page=page,
                            language_code=lang,
                            title=translated_title,
                            description=translated_description
                        )
                        created_count += 1
                        self.stdout.write(
                            f"Created translation for page '{page.title}' in language '{lang}' -> '{translated_title}'"
                        )

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(
                            f"Failed to translate page '{page.title}' in language '{lang}': {e}"
                        ))

        self.stdout.write(
            self.style.SUCCESS(f"Finished! {created_count} translation records created.")
        )
