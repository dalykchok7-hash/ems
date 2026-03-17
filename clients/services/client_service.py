from clients.models import Client
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
            Q(telephone_1__icontains=query)
        )