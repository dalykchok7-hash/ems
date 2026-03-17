import uuid
from django.db import models
from users.models import Utilisateur


class Historique(models.Model):

    ACTION_CHOICES = [
        ('connexion',          'Connexion'),
        ('deconnexion',        'Déconnexion'),
        ('creer_client',       'Créer client'),
        ('creer_abonnement',   'Créer abonnement'),
        ('creer_reservation',  'Créer réservation'),
        ('marquer_present',    'Marquer présent'),
        ('creer_vente',        'Créer vente'),
    ]

    id = models.UUIDField(
        primary_key = True,
        default     = uuid.uuid4,
        editable    = False
    )

    personnel = models.ForeignKey(
        Utilisateur,
        on_delete    = models.PROTECT,
        related_name = 'historiques'
    )

    action = models.CharField(
        max_length = 30,
        choices    = ACTION_CHOICES,
    )

    details = models.JSONField(
        default = dict,
        blank   = True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Historique'
        verbose_name_plural = 'Historiques'
        ordering            = ['-created_at']

    def __str__(self):
        return f"{self.personnel} — {self.action} — {self.created_at}"