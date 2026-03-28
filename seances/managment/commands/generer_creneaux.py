from django.core.management.base import BaseCommand
from seances.services import SeanceService
from datetime import date


class Command(BaseCommand):
    help = 'Génère les créneaux pour 365 jours'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date-debut',
            type    = str,
            default = None,
            help    = 'Date de début au format YYYY-MM-DD'
        )

    def handle(self, *args, **kwargs):
        date_debut = kwargs.get('date_debut')

        if date_debut:
            from datetime import datetime
            debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
        else:
            debut = date.today()

        created = SeanceService.generer_seances(365, date_debut=debut)
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ {created} créneaux générés depuis {debut}'
            )
        )