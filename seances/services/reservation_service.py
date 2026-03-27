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
            raise ValueError("Déjà présent")

    # 🔥 Si il était absent/annulé → reprendre place
        if reservation.statut in ['absent', 'annule']:
            if reservation.seance.places_disponibles <= 0:
                raise ValueError("Plus de places disponibles")

        reservation.seance.places_disponibles -= 1
        reservation.seance.save()

        reservation.statut = 'present'
        reservation.save()

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
            raise ValueError("Déjà annulée")

    # 🔥 Si la place était occupée → libérer
        if reservation.statut in ['en_attente', 'present']:
            reservation.seance.places_disponibles += 1
            reservation.seance.save()

        reservation.statut = 'annule'
        reservation.save()

        return reservation