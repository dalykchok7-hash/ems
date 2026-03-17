import uuid
from django.db import models
from .produit import Produit
from .vente   import Vente


class LigneVente(models.Model):

    id = models.UUIDField(
        primary_key = True,
        default     = uuid.uuid4,
        editable    = False
    )

    vente    = models.ForeignKey(
        Vente,
        on_delete    = models.CASCADE,
        related_name = 'lignes'
    )

    produit  = models.ForeignKey(
        Produit,
        on_delete    = models.PROTECT,
        related_name = 'lignes_vente'
    )

    quantite      = models.PositiveIntegerField()
    prix_unitaire = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    prix_total    = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    class Meta:
        verbose_name        = 'Ligne de vente'
        verbose_name_plural = 'Lignes de vente'

    def save(self, *args, **kwargs):
        self.prix_total = self.prix_unitaire * self.quantite
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.produit.nom} x{self.quantite} — {self.prix_total} DT"