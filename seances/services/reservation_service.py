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
        if reservation.statut != 'en_attente':
            raise ValueError(
                "Seules les réservations en attente peuvent être marquées présent"
            )

        reservation.statut = 'present'
        reservation.save()

        # Décrémenter les séances de l'abonnement
        abonnement = reservation.abonnement
        abonnement.seances_restantes -= 1
        abonnement.save()

        return reservation

    @staticmethod
    def marquer_absent(reservation):
        if reservation.statut != 'en_attente':
            raise ValueError(
                "Seules les réservations en attente peuvent être marquées absent"
            )

        reservation.statut = 'absent'
        reservation.save()

        # Libérer la place du créneau
        seance = reservation.seance
        seance.places_disponibles += 1
        seance.save()
        return reservation

    @staticmethod
    def annuler(reservation):
        if reservation.statut not in ['en_attente']:
            raise ValueError(
                "Seules les réservations en attente peuvent être annulées"
            )

        reservation.statut = 'annule'
        reservation.save()

        # Libérer la place du créneau
        seance = reservation.seance
        seance.places_disponibles += 1
        seance.save()

        return reservation