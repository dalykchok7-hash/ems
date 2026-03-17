from django.db import models
import uuid


class Seance(models.Model):

    # ── Clé primaire ─────────────────────────
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # ── Créneau ──────────────────────────────
    date        = models.DateField()

    heure_debut = models.TimeField()

    heure_fin   = models.TimeField()

    # ── Places ───────────────────────────────
    places_total = models.IntegerField(default=5)

    places_disponibles = models.IntegerField(default=5)

    # ── Dates ────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Séance'
        verbose_name_plural = 'Séances'
        ordering            = ['date', 'heure_debut']
        # Un seul créneau par date et heure
        unique_together     = ['date', 'heure_debut']

    def __str__(self):
        return f"{self.date} {self.heure_debut} ({self.places_disponibles}/{self.places_total})"

    @property
    def est_disponible(self):
        return self.places_disponibles > 0

    @property
    def est_complet(self):
        return self.places_disponibles == 0