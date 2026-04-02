from django.db import models
import uuid
from .client import Client


class Abonnement(models.Model):

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

    # ── Clé primaire ─────────────────────────────────────
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # ── Relations ────────────────────────────────────────
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='abonnements'
    )

    pack = models.ForeignKey(
        'Pack',
        on_delete=models.PROTECT,
        related_name='abonnements',
        null=True, blank=True
    )

    # ── Paiement (lié à la transaction, pas au pack) ─────
    prix_paye = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0
    )

    reduction = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text='Réduction en pourcentage (0-100)'
    )

    mode_paiement = models.CharField(
        max_length=10,
        choices=MODE_PAIEMENT_CHOICES,
        blank=True,
        default=''
    )

    est_paye = models.BooleanField(default=False)

    date_paiement = models.DateField(null=True, blank=True)

    # ── Séances ──────────────────────────────────────────
    seances_total     = models.IntegerField(default=0)
    seances_restantes = models.IntegerField(default=0)

    # ── Dates ────────────────────────────────────────────
    date_debut           = models.DateField(auto_now_add=True)
    date_derniere_seance = models.DateField(null=True, blank=True)
    date_expiration      = models.DateField(null=True, blank=True)

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
        pack_nom = self.pack.nom if self.pack else '—'
        return f"{self.client} — {pack_nom} ({self.statut})"

    def save(self, *args, **kwargs):
        if self.pack:
            # Remplir séances depuis le pack si pas encore défini
            if not self.seances_total:
                self.seances_total     = self.pack.nb_seances
                self.seances_restantes = self.pack.nb_seances

            # Calculer prix_paye = prix_pack - réduction
            prix_base  = self.pack.prix
            self.prix_paye = prix_base - (prix_base * self.reduction / 100)

        super().save(*args, **kwargs)

    @property
    def est_actif(self):
        return self.statut == 'actif'