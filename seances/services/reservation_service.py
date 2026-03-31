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

            # Vérifier séances
            if abonnement.seances_restantes <= 0:
                raise ValueError("Plus de séances disponibles")

            # Créer réservation
            reservation = Reservation.objects.create(
                abonnement=abonnement,
                seance=seance,
                personnel=personnel,
                type_appareil=type_appareil,
                taille_gilet=taille_gilet,
                statut='en_attente',
            )

            # 🔴 Réserver la place
            seance.places_disponibles = F('places_disponibles') - 1
            seance.save()

            return reservation

    @staticmethod
    def marquer_present(reservation):

        # ❌ Interdictions métier
        if reservation.statut == 'present':
            raise ValueError("Déjà présent")

        if reservation.statut == 'annule':
            raise ValueError("Réservation annulée")

        ancien_statut = reservation.statut

        with transaction.atomic():

            # 🔁 absent → present → reprendre place
            if ancien_statut == 'absent':
                if reservation.seance.places_disponibles <= 0:
                    raise ValueError("Plus de places disponibles")

                reservation.seance.places_disponibles -= 1
                reservation.seance.save()

            # 🎯 Décrémenter séance
            abonnement = reservation.abonnement

            if abonnement.statut == 'en_attente':
                abonnement.statut = 'actif'

            abonnement.seances_restantes -= 1

            if abonnement.seances_restantes <= 0:
                abonnement.statut = 'termine'

            abonnement.save()

            # ✔️ changer statut
            reservation.statut = 'present'
            reservation.save()

        return reservation

    @staticmethod
    def marquer_absent(reservation):

        # ❌ Interdictions métier
        if reservation.statut == 'absent':
            raise ValueError("Déjà absent")

        if reservation.statut == 'annule':
            raise ValueError("Réservation annulée")

        ancien_statut = reservation.statut

        with transaction.atomic():

            # 🔓 Libérer place
            if ancien_statut in ['en_attente', 'present']:
                reservation.seance.places_disponibles += 1
                reservation.seance.save()

            # 🔁 rendre séance si besoin
            if ancien_statut == 'present':
                abonnement = reservation.abonnement
                abonnement.seances_restantes += 1

                if abonnement.statut == 'termine':
                    abonnement.statut = 'actif'

                abonnement.save()

            reservation.statut = 'absent'
            reservation.save()

        return reservation

    @staticmethod
    def annuler(reservation):

        # ❌ Interdiction
        if reservation.statut == 'annule':
            raise ValueError("Déjà annulée")

        ancien_statut = reservation.statut

        with transaction.atomic():

            # 🔓 Libérer place
            if ancien_statut in ['en_attente', 'present']:
                reservation.seance.places_disponibles += 1
                reservation.seance.save()

            # 🔁 rendre séance si besoin
            if ancien_statut == 'present':
                abonnement = reservation.abonnement
                abonnement.seances_restantes += 1

                if abonnement.statut == 'termine':
                    abonnement.statut = 'actif'

                abonnement.save()

            reservation.statut = 'annule'
            reservation.save()

        return reservation