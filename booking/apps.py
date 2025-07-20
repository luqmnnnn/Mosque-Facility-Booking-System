from django.apps import AppConfig

class BookingConfig(AppConfig):  # Make sure this matches your app's name in settings.py
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'booking'

    def ready(self):
        import booking.signals  