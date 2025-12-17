# your_app/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from user_app.models import Notification
from user_app.firebase_config import send_notification
# from .tasks import send_push_notification_task
from django.core.cache import cache
# from myapp.models import WpTerms


@receiver(post_save, sender=Notification)
def send_push_notification(sender, instance, created, **kwargs):
    if not created:
        return  # only send on creation

    try:
        send_notification(instance.customer_id, instance.title, instance.body, {}, instance.user_id)
    except Exception as e:
        print(f"[Signal Error] Failed to send push: {e}")

