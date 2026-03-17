from clients.models import Abonnement, Client


class AbonnementService:

    @staticmethod
    def creer_abonnement(client, data):
        # Vérifier abonnement actif existant
        if client.abonnement_actif:
            raise ValueError("Ce client a déjà un abonnement actif")

        abonnement = Abonnement.objects.create(
            client          = client,
            type            = data['type'],
            mode_paiement   = data.get('mode_paiement', ''),
            est_paye        = data.get('est_paye', False),
            date_paiement   = data.get('date_paiement', None),
            date_expiration = data.get('date_expiration', None),
            reduction       = data.get('reduction', 0),
        )
        return abonnement

    @staticmethod
    def modifier_abonnement(abonnement, data):
        for champ in ['mode_paiement', 'est_paye',
                      'date_paiement', 'date_expiration', 'reduction']:
            if champ in data:
                setattr(abonnement, champ, data[champ])

        abonnement.save()
        return abonnement

    @staticmethod
    def historique_abonnements(client):
        return Abonnement.objects.filter(
            client = client
        ).order_by('-created_at')