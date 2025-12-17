from googletrans import Translator
from django.core.management.base import BaseCommand
from management_app.models import Client, ClientTranslation


class Command(BaseCommand):
    help = "Create translation records for existing clients in multiple languages"

    LANGUAGES = ['hi', 'mr', 'gu', 'bn', 'ta', 'te', 'kn', 'ml', 'pa'] 

    def handle(self, *args, **kwargs):
        translator = Translator()
        created_count = 0

        for client in Client.objects.all():
            for lang in self.LANGUAGES:
                if not ClientTranslation.objects.filter(client=client, language_code=lang).exists():
                    try:
                        translated_name = translator.translate(client.name, src='en', dest=lang).text
                        translated_description = None
                        if client.description:
                            translated_description = translator.translate(client.description, src='en', dest=lang).text

                        # Create translation entry
                        ClientTranslation.objects.create(
                            client=client,
                            language_code=lang,
                            name=translated_name,
                            description=translated_description,
                        )

                        created_count += 1
                        self.stdout.write(
                            f"Created translation for client '{client.name}' in '{lang}' -> '{translated_name}'"
                        )

                    except Exception as e:
                        self.stderr.write(
                            self.style.ERROR(f"Error translating client '{client.name}' to '{lang}': {e}")
                        )

        self.stdout.write(
            self.style.SUCCESS(f"Finished! {created_count} client translation records created.")
        )
