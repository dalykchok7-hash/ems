from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import Utilisateur
from clients.models import Client


class ClientTestCase(TestCase):

    def setUp(self):
        self.client_api = APIClient()

        # Créer admin
        self.admin = Utilisateur.objects.create_superuser(
            username = 'admin_test',
            password = 'admin1234',
            email    = 'admin@test.com',
            cin      = '99999999',
            role     = 'admin',
        )

        # Créer personnel
        self.personnel = Utilisateur.objects.create_user(
            username = 'karim_test',
            password = 'karim1234',
            email    = 'karim@test.com',
            cin      = '88888888',
            role     = 'personnel',
        )

        # Tokens
        login = self.client_api.post('/api/users/login/', {
            'username': 'admin_test',
            'password': 'admin1234'
        })
        self.token_admin = login.data['access']

        login2 = self.client_api.post('/api/users/login/', {
            'username': 'karim_test',
            'password': 'karim1234'
        })
        self.token_personnel = login2.data['access']

        # Créer client de test
        self.client_test = Client.objects.create(
            nom         = 'Ben Ali',
            prenom      = 'Mohamed',
            cin         = '12345678',
            telephone_1 = '55123456',
        )

    # ── Tests liste clients ──────────────────

    def test_liste_clients_avec_token(self):
        self.client_api.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.token_admin}'
        )
        response = self.client_api.get('/api/clients/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIsInstance(response.data['results'], list)

    def test_liste_clients_sans_token_refuse(self):
        self.client_api.credentials()
        response = self.client_api.get('/api/clients/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_liste_clients_personnel_autorise(self):
        self.client_api.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.token_personnel}'
        )
        response = self.client_api.get('/api/clients/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ── Tests recherche ──────────────────────

    def test_recherche_par_nom(self):
        self.client_api.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.token_admin}'
        )
        response = self.client_api.get('/api/clients/?q=Ben Ali')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)

    def test_recherche_par_cin(self):
        self.client_api.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.token_admin}'
        )
        response = self.client_api.get('/api/clients/?q=12345678')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_recherche_inexistante(self):
        self.client_api.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.token_admin}'
        )
        response = self.client_api.get('/api/clients/?q=xxxxxxxx')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    # ── Tests créer client ───────────────────

    def test_creer_client_correct(self):
        self.client_api.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.token_admin}'
        )
        response = self.client_api.post('/api/clients/', {
            'nom'         : 'Slim',
            'prenom'      : 'Yassine',
            'cin'         : '11223344',
            'telephone_1' : '99887766',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['cin'], '11223344')

    def test_creer_client_cin_duplique(self):
        self.client_api.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.token_admin}'
        )
        response = self.client_api.post('/api/clients/', {
            'nom'         : 'Dupliquer',
            'prenom'      : 'Test',
            'cin'         : '12345678',  # ← déjà existant
            'telephone_1' : '11223344',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_creer_client_champs_manquants(self):
        self.client_api.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.token_admin}'
        )
        response = self.client_api.post('/api/clients/', {
            'nom': 'Slim',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_creer_plusieurs_clients(self):
        self.client_api.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.token_admin}'
        )
        clients_data = [
            {'nom': 'Client1', 'prenom': 'Test', 'cin': '11111111', 'telephone_1': '11111111'},
            {'nom': 'Client2', 'prenom': 'Test', 'cin': '22222222', 'telephone_1': '22222222'},
            {'nom': 'Client3', 'prenom': 'Test', 'cin': '33333333', 'telephone_1': '33333333'},
            {'nom': 'Client4', 'prenom': 'Test', 'cin': '44444444', 'telephone_1': '44444444'},
            {'nom': 'Client5', 'prenom': 'Test', 'cin': '55555555', 'telephone_1': '55555555'},
        ]
        for data in clients_data:
            response = self.client_api.post('/api/clients/', data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        total = Client.objects.count()
        self.assertEqual(total, 6)  # 5 nouveaux + 1 setUp

    # ── Tests détail client ──────────────────

    def test_detail_client_existant(self):
        self.client_api.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.token_admin}'
        )
        response = self.client_api.get('/api/clients/12345678/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cin'], '12345678')

    def test_detail_client_inexistant(self):
        self.client_api.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.token_admin}'
        )
        response = self.client_api.get('/api/clients/00000000/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ── Tests modifier client ────────────────

    def test_modifier_client_telephone(self):
        self.client_api.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.token_admin}'
        )
        response = self.client_api.put('/api/clients/12345678/', {
            'telephone_1': '99999999',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)