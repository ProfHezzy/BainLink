# signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType # <--- IMPORT THIS
from .models import Profile, Message, Notification # Ensure Notification is imported here

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile = Profile.objects.create(user=instance)
        if instance.is_superuser:
            profile.bio = "System Administrator"
            profile.save()

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Save profile whenever user is saved (optional, but good for syncing changes)
    instance.profile.save()

@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    if created:
        # No need to import Notification inside if it's imported at the top
        Notification.objects.create(
            recipient=instance.recipient,
            sender=instance.sender,
            notification_type='message', # Consider changing to 'new_message' for consistency with views.py
            message=f"New message from {instance.sender.username}",
            # Use content_type and object_id for Generic Foreign Key
            content_type=ContentType.objects.get_for_model(instance), # Get ContentType for the Message instance
            object_id=instance.id # Use the ID of the Message instance
        )