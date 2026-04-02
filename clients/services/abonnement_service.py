from clients.models import Abonnement, Client, Pack


class AbonnementService:

    @staticmethod
    def creer_abonnement(client, data):
        # Vérifier abonnement actif existant
        if client.abonnement_actif:
            raise ValueError("Ce client a déjà un abonnement actif")

        # Récupérer le pack choisi
        try:
            pack = Pack.objects.get(id=data['pack_id'], est_actif=True)
        except Pack.DoesNotExist:
            raise ValueError("Pack introuvable ou désactivé")

        abonnement = Abonnement.objects.create(
            client          = client,
            pack            = pack,
            # ← paiement : propre à cette transaction
            mode_paiement   = data.get('mode_paiement', ''),
            est_paye        = data.get('est_paye', False),
            date_paiement   = data.get('date_paiement', None),
            date_expiration = data.get('date_expiration', None),
            reduction       = data.get('reduction', 0),
            # seances_total, seances_restantes et prix_paye
            # sont calculés automatiquement dans Abonnement.save()
        )
        return abonnement

    @staticmethod
    def modifier(abonnement_id, data):
        try:
            abonnement = Abonnement.objects.get(id=abonnement_id)
        except Abonnement.DoesNotExist:
            return {'error': 'Abonnement introuvable'}

        champs_modifiables = [
            'mode_paiement',
            'est_paye',
            'date_paiement',
            'date_expiration',
            'reduction',
        ]
        for champ in champs_modifiables:
            if champ in data:
                setattr(abonnement, champ, data[champ])

        abonnement.save()
        return abonnement

    @staticmethod
    def supprimer(abonnement_id):
        try:
            abonnement = Abonnement.objects.get(id=abonnement_id)
        except Abonnement.DoesNotExist:
            return {'error': 'Abonnement introuvable'}

        abonnement.delete()
        return {'message': 'Abonnement supprimé avec succès'}

    @staticmethod
    def historique_abonnements(client):
        return Abonnement.objects.filter(
            client=client
        ).order_by('-created_at')


class PackService:

    @staticmethod
    def creer_pack(data):
        return Pack.objects.create(
            nom         = data['nom'],
            nb_seances  = data['nb_seances'],
            prix        = data['prix'],
            description = data.get('description', ''),
        )

    @staticmethod
    def modifier_pack(pack_id, data):
        try:
            pack = Pack.objects.get(id=pack_id)
        except Pack.DoesNotExist:
            return {'error': 'Pack introuvable'}

        for champ, valeur in data.items():
            setattr(pack, champ, valeur)
        pack.save()
        return pack

    @staticmethod
    def desactiver_pack(pack_id):
        try:
            pack = Pack.objects.get(id=pack_id)
        except Pack.DoesNotExist:
            return {'error': 'Pack introuvable'}

        pack.est_actif = False
        pack.save()
        return {'message': f"Pack '{pack.nom}' désactivé"}