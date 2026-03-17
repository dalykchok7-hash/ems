from django.db import models
from django.db.models import F
from django.db import transaction
import uuid
from .seance import Seance
from clients.models import Abonnement
from users.models import Utilisateur


class Reservation(models.Model):

    STATUT_CHOICES = [
        ('en_attente', 'En Attente'),
        ('present',    'Présent'),
        ('absent',     'Absent'),
        ('annule',     'Annulé'),
    ]

    TYPE_APPAREIL_CHOICES = [
        ('i-motion', 'i-Motion'),
        ('i-model',  'i-Model'),
    ]

    # ── Clé primaire ─────────────────────────
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # ── Relations ────────────────────────────
    abonnement = models.ForeignKey(
        Abonnement,
        on_delete=models.PROTECT,
        related_name='reservations'
    )

    seance = models.ForeignKey(
        Seance,
        on_delete=models.PROTECT,
        related_name='reservations'
    )

    personnel = models.ForeignKey(
        Utilisateur,
        on_delete=models.PROTECT,
        related_name='reservations_creees'
    )

    # ── Détails ───────────────────────────────
    type_appareil = models.CharField(
        max_length=10,
        choices=TYPE_APPAREIL_CHOICES
    )

    statut = models.CharField(
        max_length=15,
        choices=STATUT_CHOICES,
        default='en_attente'
    )

    # ── Rattrapage ────────────────────────────
    est_rattrapage = models.BooleanField(default=False)

    # ── Dates ────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Réservation'
        verbose_name_plural = 'Réservations'
        ordering            = ['-created_at']

    def __str__(self):
        return f"{self.abonnement.client} — {self.seance} ({self.statut})"

    def marquer_present(self):
        with transaction.atomic():
            # 1. Mettre à jour le statut réservation
            self.statut = 'present'
            self.save()

            # 2. Activer l'abonnement si en_attente
            abonnement = self.abonnement
            if abonnement.statut == 'en_attente':
                abonnement.statut ='actif'
                abonnement.save()

            # 3. Décrémenter les séances
            abonnement.seances_restantes = F('seances_restantes') - 1
            abonnement.date_derniere_seance = abonnement.date_derniere_seance
            abonnement.save()

            # Recharger depuis la DB pour avoir la valeur réelle
            abonnement.refresh_from_db()

            # 4. Si type essai → marquer essai_fait
            if abonnement.type == 'essai':
                abonnement.client.essai_fait = True
                abonnement.client.save()

            # 5. Si plus de séances → terminer
            if abonnement.seances_restantes == 0:
                abonnement.statut = 'termine'
                abonnement.save()

    def marquer_absent(self):
        with transaction.atomic():
            self.statut = 'absent'
            self.save()

    def annuler(self):
        with transaction.atomic():
            # Libérer la place dans le créneau
            self.seance.places_disponibles = F('places_disponibles') + 1
            self.seance.save()

            self.statut = 'annule'
            self.save()