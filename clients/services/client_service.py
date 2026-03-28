from clients.models import Client
from seances.models import Reservation
from django.db.models import Q


class ClientService:

    @staticmethod
    def creer_client(data):
        if Client.objects.filter(cin=data['cin']).exists():
            raise ValueError("Un client avec ce CIN existe déjà")

        client = Client.objects.create(
            nom            = data['nom'],
            prenom         = data['prenom'],
            cin            = data['cin'],
            telephone_1    = data['telephone_1'],
            telephone_2    = data.get('telephone_2', ''),
            email          = data.get('email', ''),
            date_naissance = data.get('date_naissance', None),
            photo          = data.get('photo', None),    # ← ajouter
    )
        
        return client

    @staticmethod
    def modifier_client(client, data):
        nouveau_cin = data.get('cin')
        if nouveau_cin and nouveau_cin != client.cin:
            if Client.objects.filter(cin=nouveau_cin).exists():
                raise ValueError("Un client avec ce CIN existe déjà")

        for champ in ['nom', 'prenom', 'cin', 'telephone_1',
                      'telephone_2', 'email', 'date_naissance', 'photo']:
            if champ in data:
                setattr(client, champ, data[champ])

        client.save()
        return client

    @staticmethod
    def rechercher_clients(query):
        return Client.objects.filter(
            Q(cin__icontains=query)         |
            Q(nom__icontains=query)         |
            Q(prenom__icontains=query)      |
            Q(telephone_1__icontains=query),
            filter(statut='actif')
        )


    @staticmethod
    def supprimer_client(client):

        # récupérer les réservations actives
        reservations = Reservation.objects.filter(
            abonnement__client=client,
            statut__in=['en_attente', 'present']
        ).select_related('seance')

        # libérer les places
        for r in reservations:
            seance = r.seance
            seance.places_disponibles += 1
            seance.save()

        # supprimer le client (cascade auto)
        client.statut = 'inactif'
        client.save()