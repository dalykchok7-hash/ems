from django.db import models
import uuid


class Client(models.Model):

    STATUT_CHOICES = [
        ('actif',   'Actif'),
        ('inactif', 'Inactif'),
    ]

    # ── Clé primaire ─────────────────────────
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # ── Identité ─────────────────────────────
    nom = models.CharField(max_length=100)

    prenom = models.CharField(max_length=100)

    cin = models.CharField(
        max_length=20,
        unique=True
    )

    telephone_1 = models.CharField(max_length=20)

    telephone_2 = models.CharField(
        max_length=20,
        blank=True,
        default=''
    )

    email = models.EmailField(
        blank=True,
        default=''
    )

    date_naissance = models.DateField(
        null=True,
        blank=True
    )

    photo = models.ImageField(
        upload_to='clients/',
        null=True,
        blank=True
    )

    # ── Métier ───────────────────────────────
    essai_fait = models.BooleanField(default=False)

    statut = models.CharField(
        max_length=10,
        choices=STATUT_CHOICES,
        default='actif'
    )

    # ── Dates ────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Client'
        verbose_name_plural = 'Clients'
        ordering            = ['-created_at']

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.cin})"

    @property
    def abonnement_actif(self):
        return self.abonnements.filter(
            statut__in=['actif', 'en_attente']
        ).first()