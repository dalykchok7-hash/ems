from django.db import transaction
from produits.models import Vente, LigneVente


class VenteService:

    @staticmethod
    def creer_vente(lignes, personnel):
        with transaction.atomic():
            # Créer la vente
            vente = Vente.objects.create(
                personnel = personnel,
                prix_total = 0
            )

            # Créer les lignes et décrémenter le stock
            for ligne in lignes:
                produit  = ligne['produit']
                quantite = ligne['quantite']

                LigneVente.objects.create(
                    vente         = vente,
                    produit       = produit,
                    quantite      = quantite,
                    prix_unitaire = produit.prix_unitaire,
                )

                # Décrémenter le stock
                produit.stock -= quantite
                produit.save()

            # Calculer le total
            vente.calculer_total()

            return vente

    @staticmethod
    def historique(date_param=None):
        from datetime import date

        ventes = Vente.objects.all().prefetch_related(
            'lignes__produit'
        ).select_related('personnel')

        if date_param:
            ventes = ventes.filter(created_at__date=date_param)

        return ventes