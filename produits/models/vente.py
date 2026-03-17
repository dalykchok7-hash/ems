import uuid
from django.db import models
from users.models import Utilisateur


class Vente(models.Model):

    id = models.UUIDField(
        primary_key = True,
        default     = uuid.uuid4,
        editable    = False
    )

    personnel  = models.ForeignKey(
        Utilisateur,
        on_delete    = models.PROTECT,
        related_name = 'ventes'
    )

    prix_total = models.DecimalField(
        max_digits     = 8,
        decimal_places = 2,
        default        = 0
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Vente'
        verbose_name_plural = 'Ventes'
        ordering            = ['-created_at']

    def __str__(self):
        return f"Vente {self.id} — {self.prix_total} DT"

    def calculer_total(self):
        total = sum(
            ligne.prix_total for ligne in self.lignes.all()
        )
        self.prix_total = total
        self.save()