from django.db import models
import uuid


class Pack(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    nom = models.CharField(max_length=100)      # ex: "Pack 10", "VIP", "Essai"
    nb_seances = models.IntegerField()           # nombre de séances incluses
    prix = models.DecimalField(                  # prix de base sans réduction
        max_digits=8,
        decimal_places=2
    )
    description = models.TextField(blank=True, default='')
    est_actif   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Pack'
        verbose_name_plural = 'Packs'
        ordering            = ['prix']

    def __str__(self):
        return f"{self.nom} ({self.nb_seances} séances — {self.prix} DT)"