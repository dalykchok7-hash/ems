from django.apps import AppConfig


class SeancesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'seances'

    def ready(self):
        import django
        from django.db import connection
        try:
            if connection.vendor:
                from seances.services import SeanceService
                SeanceService.verifier_et_generer()
        except Exception:
            pass