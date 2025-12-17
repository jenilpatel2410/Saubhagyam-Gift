from django.apps import AppConfig


class UserAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user_app'

    def ready(self):
        import user_app.signals
        try:
            from .firebase_config import initialize_firebase
            initialize_firebase()
        except Exception as e:
            print(f"Error initializing Firebase: {str(e)}")
    