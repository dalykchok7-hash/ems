from seances.models import Reservation


class ReservationService:

    @staticmethod
    def creer_reservation(abonnement, seance, type_appareil, personnel, taille_gilet=None):
        deja_reserve = Reservation.objects.filter(
            abonnement__client = abonnement.client,
            seance             = seance,
            statut__in         = ['en_attente', 'present']
        ).exists()
        if deja_reserve:
            raise ValueError(
            "Ce client a déjà une réservation dans ce créneau"
        )
        # Créer la réservation

        reservation = Reservation.objects.create(
            abonnement    = abonnement,
            seance        = seance,
            personnel     = personnel,
            type_appareil = type_appareil,
            taille_gilet  = taille_gilet,
            statut        = 'en_attente',
        )

        # Décrémenter les places du créneau
        seance.places_disponibles -= 1
        seance.save()

        return reservation

    @staticmethod
    def marquer_present(reservation):

        if reservation.statut == 'present':
         return reservation  # rien à faire

    # 🔁 si absent → on reprend la place
        if reservation.statut == 'absent':
            reservation.seance.places_disponibles -= 1
            reservation.seance.save()

    # ❌ si annulé → interdit
        if reservation.statut == 'annule':
            raise ValueError("Impossible de marquer une réservation annulée")

        reservation.statut = 'present'
        reservation.save()

    # ⚠️ décrémenter seulement une fois
        abonnement = reservation.abonnement
        if reservation.statut != 'present':  # sécurité inutile ici mais ok
            abonnement.seances_restantes -= 1
            abonnement.save()

        return reservation

    @staticmethod
    def marquer_absent(reservation):

        if reservation.statut == 'absent':
            return reservation

    # 🔁 si present → remettre séance
        if reservation.statut == 'present':
            reservation.abonnement.seances_restantes += 1
            reservation.abonnement.save()

        # ❌ si annulé → interdit
        if reservation.statut == 'annule':
            raise ValueError("Impossible de modifier une réservation annulée")

        reservation.statut = 'absent'
        reservation.save()

    # libérer place
        reservation.seance.places_disponibles += 1
        reservation.seance.save()

        return reservation

    @staticmethod
    def annuler(reservation):

        if reservation.statut == 'annule':
            return reservation

    # ❌ interdit si déjà consommé (optionnel selon business)
    # if reservation.statut == 'present':
    #     raise ValueError("Impossible d'annuler une séance déjà effectuée")

    # 🔁 si present → remettre séance
        if reservation.statut == 'present':
            reservation.abonnement.seances_restantes += 1
            reservation.abonnement.save()

    # 🔁 si en_attente → libérer place
        if reservation.statut == 'en_attente':
            reservation.seance.places_disponibles += 1
            reservation.seance.save()

    # 🔁 si absent → ne rien faire (déjà libéré)

        reservation.statut = 'annule'
        reservation.save()

        return reservation