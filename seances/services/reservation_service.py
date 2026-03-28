from seances.models import Reservation
from django.db import transaction
from django.db.models import F

class ReservationService:

    @staticmethod
    def creer_reservation(abonnement, seance, type_appareil, personnel, taille_gilet=None):
        with transaction.atomic():

        # Vérifier doublon
            if Reservation.objects.filter(
                abonnement=abonnement,
                seance=seance,
                statut__in=['en_attente', 'present']
            ).exists():
                raise ValueError("Client déjà réservé")

        # Vérifier places
        if seance.places_disponibles <= 0:
            raise ValueError("Créneau complet")

        # Créer réservation
        reservation = Reservation.objects.create(
            abonnement=abonnement,
            seance=seance,
            personnel=personnel,
            type_appareil=type_appareil,
            taille_gilet=taille_gilet,
            statut='en_attente',
        )

        # Décrémenter proprement
        seance.places_disponibles = F('places_disponibles') - 1
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
        if reservation.statut not in ['en_attente', 'present']:  # ← ajouter present
            raise ValueError(
            "Seules les réservations en attente ou présentes peuvent être annulées"
        )

        reservation.statut = 'annule'
        reservation.save()

    # Libérer la place du créneau
        seance = reservation.seance
        seance.places_disponibles += 1
        seance.save()

    # Si present → remettre les séances de l'abonnement
        if reservation.statut == 'annule':
            pass  # déjà sauvegardé

        return reservation