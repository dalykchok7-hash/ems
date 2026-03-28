from seances.models import Reservation
from django.db import transaction
from django.db.models import  F                                              

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

        # Décrémenter proprement
        seance.places_disponibles = F('places_disponibles') - 1
        seance.save()

        return reservation

    @staticmethod
    def marquer_present(reservation):
        ancien_statut = reservation.statut

        with transaction.atomic():
            # Si venait de absent → reprendre une place
            if ancien_statut == 'absent':
                if reservation.seance.places_disponibles <= 0:
                    raise ValueError("Plus de places disponibles")
                reservation.seance.places_disponibles -= 1
                reservation.seance.save()

            # Décrémenter séances seulement si pas déjà présent
            if ancien_statut != 'present':
                reservation.abonnement.seances_restantes -= 1
                reservation.abonnement.save()

            reservation.statut = 'present'
            reservation.save()

        return reservation

    @staticmethod
    def marquer_absent(reservation):
        ancien_statut = reservation.statut

        with transaction.atomic():
            # Libérer place seulement si en_attente ou present
            if ancien_statut in ['en_attente', 'present']:
                reservation.seance.places_disponibles += 1
                reservation.seance.save()

            # Remettre séance seulement si venait de present
            if ancien_statut == 'present':
                reservation.abonnement.seances_restantes += 1
                reservation.abonnement.save()

            reservation.statut = 'absent'
            reservation.save()

        return reservation

    @staticmethod
    def annuler(reservation):
        ancien_statut = reservation.statut

        with transaction.atomic():
            # Libérer place si en_attente ou present
            if ancien_statut in ['en_attente', 'present']:
                reservation.seance.places_disponibles += 1
                reservation.seance.save()

            # Remettre séance si venait de present
            if ancien_statut == 'present':
                reservation.abonnement.seances_restantes += 1
                reservation.abonnement.save()

            reservation.statut = 'annule'
            reservation.save()

        return reservation