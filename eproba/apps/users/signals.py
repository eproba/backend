from django.contrib.auth import get_user_model
from django.db.models.signals import pre_save
from django.dispatch import receiver
from oauth2_provider.models import AccessToken, RefreshToken

User = get_user_model()


@receiver(pre_save, sender=User)
def user_deactivated(sender: User, instance: User, **kwargs):
    if instance.pk:
        try:
            previous = sender.objects.get(pk=instance.pk)
            if previous and previous.is_active and not instance.is_active:
                AccessToken.objects.filter(user=instance).delete()
                RefreshToken.objects.filter(user=instance).delete()
                instance.function = 0
                instance.is_staff = False
        except sender.DoesNotExist:
            # User is being created for the first time, no tokens to deactivate
            pass
