from datetime import date, timedelta, time
from seances.models import Seance


class SeanceService:

    @staticmethod
    def generer_seances(jours=365, date_debut=None):
        if date_debut is None:
            date_debut = date.today()

        seances_a_creer = []

        # Récupérer les créneaux existants
        existants = set(
            Seance.objects.filter(
                date__gte=date_debut
            ).values_list('date', 'heure_debut')
        )

        for i in range(jours):
            jour = date_debut + timedelta(days=i)

            for heure in range(8,22):
                for minute in [0, 30]:  
                    heure_debut = time(heure, minute)

                    # Ignorer si existe déjà
                    if (jour, heure_debut) in existants:
                        continue

                    if minute == 0:
                        heure_fin = time(heure, 30)
                    else:
                         heure_fin = time(heure + 1, 0)  # ← 21:30 → 22:00 ✅
                         
                    if (jour, heure_debut) in existants:
                        continue

                    seances_a_creer.append(
                        Seance(
                            date               = jour,
                            heure_debut        = heure_debut,
                            heure_fin          = heure_fin,
                            places_total       = 3,
                            places_disponibles = 3,
                        )
                    )

        # Créer tout en une seule requête
        if seances_a_creer:
            Seance.objects.bulk_create(seances_a_creer)

        return len(seances_a_creer)

    @staticmethod
    def verifier_et_generer():
        derniere_seance = Seance.objects.order_by('-date').first()

        if not derniere_seance:
            SeanceService.generer_seances(365)
            return

        aujourd_hui    = date.today()
        dernier_jour   = derniere_seance.date
        jours_restants = (dernier_jour - aujourd_hui).days

        if jours_restants < 300:
            SeanceService.generer_seances(365)