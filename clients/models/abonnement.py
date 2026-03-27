from django.db import models
import uuid
from .client import Client


class Abonnement(models.Model):

    TYPE_CHOICES = [
    ('essai',   'Essai'),
    ('unique', 'Unique'),
    ('pack5',  'Pack 5'),
    ('pack10',  'Pack 10'),
    ('pack20',  'Pack 20'),
    ('pack30',  'Pack 30'),
]

    MODE_PAIEMENT_CHOICES = [
        ('cash', 'Cash'),
        ('tpe',  'TPE'),
    ]

    STATUT_CHOICES = [
        ('en_attente', 'En Attente'),
        ('actif',      'Actif'),
        ('expiré',     'Expiré'),
        ('terminé',    'Terminé'),
    ]

    SEANCES_PAR_TYPE = {
        'essai': 1,
        'unique':1,
        'pack5' :5,
        'pack10':10,
        'pack20':20,
        'pack30':30,
    }

    PRIX_PAR_TYPE = {
        'essai':45,
        'unique':60,
        'pack5' :250,
        'pack10':550,
        'pack20':920,
        'pack30':1150,
    }

    # ── Clé primaire ─────────────────────────
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # ── Relations ────────────────────────────
    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name='abonnements'
    )

    # ── Type et prix ─────────────────────────
    type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES
    )

    prix_paye = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0
    )

    reduction = models.DecimalField(
    max_digits   = 5,
    decimal_places = 2,
    default      = 0,
    help_text    = "Réduction en pourcentage (0-100)"
    )

    mode_paiement = models.CharField(
        max_length=10,
        choices=MODE_PAIEMENT_CHOICES,
        blank=True,
        default=''
    )

    est_paye = models.BooleanField(default=False)

    date_paiement = models.DateField(
        null=True,
        blank=True
    )

    # ── Séances ──────────────────────────────
    seances_total = models.IntegerField(default=0)

    seances_restantes = models.IntegerField(default=0)

    # ── Dates ────────────────────────────────
    date_debut = models.DateField(auto_now_add=True)

    date_derniere_seance = models.DateField(
        null=True,
        blank=True
    )

    date_expiration = models.DateField(
        null=True,
        blank=True
    )

    statut = models.CharField(
        max_length=15,
        choices=STATUT_CHOICES,
        default='en_attente'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Abonnement'
        verbose_name_plural = 'Abonnements'
        ordering            = ['-created_at']

    def __str__(self):
        return f"{self.client} — {self.get_type_display()} ({self.statut})"

    def save(self, *args, **kwargs):
        # Vérifier essai déjà fait
        if self.type == 'essai' and self.client.essai_fait:
            raise ValueError("Ce client a déjà bénéficié d'une séance d'essai")

        # Remplir séances automatiquement
        if not self.seances_total:
            self.seances_total    = self.SEANCES_PAR_TYPE[self.type]
            self.seances_restantes = self.seances_total

        # Calculer prix avec réduction
        prix_normal = self.PRIX_PAR_TYPE[self.type]
        self.prix_paye = prix_normal - (prix_normal * self.reduction / 100)

        super().save(*args, **kwargs)

    @property
    def est_actif(self):
        return self.statut == 'actif'