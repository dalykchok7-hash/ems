from historique.models import Historique


class HistoriqueService:

    @staticmethod
    def log(personnel, action, details=None):
        Historique.objects.create(
            personnel = personnel,
            action    = action,
            details   = details or {}
        )

    @staticmethod
    def connexion(personnel):
        HistoriqueService.log(
            personnel = personnel,
            action    = 'connexion',
            details   = {'username': personnel.username}
        )

    @staticmethod
    def deconnexion(personnel):
        HistoriqueService.log(
            personnel = personnel,
            action    = 'deconnexion',
            details   = {'username': personnel.username}
        )

    @staticmethod
    def creer_client(personnel, client):
        HistoriqueService.log(
            personnel = personnel,
            action    = 'creer_client',
            details   = {
                'client_cin'  : client.cin,
                'client_nom'  : f"{client.prenom} {client.nom}",
            }
        )

    @staticmethod
    def creer_abonnement(personnel, abonnement):
        HistoriqueService.log(
            personnel = personnel,
            action    = 'creer_abonnement',
            details   = {
                'client_cin'  : abonnement.client.cin,
                'client_nom'  : f"{abonnement.client.prenom} {abonnement.client.nom}",
                'type'        : abonnement.pack.nom if abonnement.pack else '—',
                'prix_paye'   : str(abonnement.prix_paye),
            }
        )

    @staticmethod
    def creer_reservation(personnel, reservation):
        HistoriqueService.log(
            personnel = personnel,
            action    = 'creer_reservation',
            details   = {
                'client_cin'   : reservation.abonnement.client.cin,
                'client_nom'   : f"{reservation.abonnement.client.prenom} {reservation.abonnement.client.nom}",
                'seance_date'  : str(reservation.seance.date),
                'seance_heure' : str(reservation.seance.heure_debut),
                'type_appareil': reservation.type_appareil,
            }
        )

    @staticmethod
    def marquer_present(personnel, reservation):
        HistoriqueService.log(
            personnel = personnel,
            action    = 'marquer_present',
            details   = {
                'client_cin'   : reservation.abonnement.client.cin,
                'client_nom'   : f"{reservation.abonnement.client.prenom} {reservation.abonnement.client.nom}",
                'seance_date'  : str(reservation.seance.date),
                'seance_heure' : str(reservation.seance.heure_debut),
            }
        )

    @staticmethod
    def creer_vente(personnel, vente):
        lignes = [
            {
                'produit'  : ligne.produit.nom,
                'quantite' : ligne.quantite,
                'total'    : str(ligne.prix_total),
            }
            for ligne in vente.lignes.all()
        ]
        HistoriqueService.log(
            personnel = personnel,
            action    = 'creer_vente',
            details   = {
                'prix_total' : str(vente.prix_total),
                'lignes'     : lignes,
            }
        )

    @staticmethod
    def liste_par_date(date_param):
        return Historique.objects.select_related('personnel').filter(
            created_at__date=date_param
        )

    @staticmethod
    def liste_intervalle(date_debut, date_fin):
        return Historique.objects.select_related('personnel').filter(
            created_at__date__gte=date_debut,
            created_at__date__lte=date_fin
        )