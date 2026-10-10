from django.apps import AppConfig


class MappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mapp'
    def ready(self):
        import mapp.signals