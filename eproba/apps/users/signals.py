from django.contrib.auth import get_user_model
from django.db.models.signals import pre_save
from django.dispatch import receiver
from oauth2_provider.models import AccessToken, RefreshToken

User = get_user_model()


@receiver(pre_save, sender=User)
def deactivate_tokens(sender, instance, **kwargs):
    if instance.pk:
        previous = sender.objects.get(pk=instance.pk)
        if previous and previous.is_active and not instance.is_active:
            AccessToken.objects.filter(user=instance).delete()
            RefreshToken.objects.filter(user=instance).delete()
