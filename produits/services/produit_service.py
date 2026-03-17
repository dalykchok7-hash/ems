from produits.models import Produit


class ProduitService:

    @staticmethod
    def creer(data):
        produit = Produit.objects.create(
            nom           = data['nom'],
            type          = data['type'],
            prix_unitaire = data['prix_unitaire'],
            stock         = data['stock'],
            seuil_alerte  = data.get('seuil_alerte', 2),
        )
        return produit

    @staticmethod
    def modifier(produit_id, data):
        try:
            produit = Produit.objects.get(id=produit_id)
        except Produit.DoesNotExist:
            return {'error': 'Produit non trouvé'}

        for champ in ['nom', 'prix_unitaire', 'stock', 'seuil_alerte', 'est_actif']:
            if champ in data:
                setattr(produit, champ, data[champ])

        produit.save()
        return produit

    @staticmethod
    def liste(actifs_seulement=True):
        if actifs_seulement:
            return Produit.objects.filter(est_actif=True)
        return Produit.objects.all()

    @staticmethod
    def stock_faible():
        return Produit.objects.filter(
            est_actif = True,
            stock__lte = 2
        )