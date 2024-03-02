def clear_tokens():
    from oauth2_provider.models import clear_expired

    clear_expired()
