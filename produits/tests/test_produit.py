from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import Utilisateur
from produits.models import Produit


class ProduitTestCase(TestCase):

    def setUp(self):
        self.client_api = APIClient()

        # ── Users ─────────────────────────────
        self.admin = Utilisateur.objects.create_superuser(
            username='admin_test',
            password='admin1234',
            email='admin@test.com',
            cin='99999999',
            role='admin',
        )

        self.personnel = Utilisateur.objects.create_user(
            username='pers_test',
            password='pers1234',
            email='pers@test.com',
            cin='88888888',
            role='personnel',
        )

        # ── Tokens ────────────────────────────
        login = self.client_api.post('/api/users/login/', {
            'username': 'admin_test',
            'password': 'admin1234'
        })
        self.token_admin = login.data['access']

        login2 = self.client_api.post('/api/users/login/', {
            'username': 'pers_test',
            'password': 'pers1234'
        })
        self.token_personnel = login2.data['access']

        # ── Produit test ──────────────────────
        self.produit = Produit.objects.create(
            nom="Whey Protein",
            type="complement",
            prix_unitaire=100,
            stock=10,
            seuil_alerte=2
        )

    # ── LISTE ───────────────────────────────

    def test_liste_produits_admin(self):
        self.client_api.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        response = self.client_api.get('/api/produits/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_liste_produits_personnel(self):
        self.client_api.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_personnel}')
        response = self.client_api.get('/api/produits/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_liste_sans_token(self):
        response = self.client_api.get('/api/produits/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── CREATION ────────────────────────────

    def test_creer_produit_admin(self):
        self.client_api.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        response = self.client_api.post('/api/produits/', {
            "nom": "Creatine",
            "type": "complement",
            "prix_unitaire": 50,
            "stock": 20
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_creer_produit_personnel_refuse(self):
        self.client_api.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_personnel}')
        response = self.client_api.post('/api/produits/', {
            "nom": "BCAA",
            "type": "complement",
            "prix_unitaire": 30,
            "stock": 10
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ── MODIFICATION ───────────────────────

    def test_modifier_produit_admin(self):
        self.client_api.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        response = self.client_api.put(f'/api/produits/{self.produit.id}/', {
            "stock": 99
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_modifier_produit_inexistant(self):
        import uuid
        fake_id = uuid.uuid4()

        self.client_api.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        response = self.client_api.put(f'/api/produits/{fake_id}/', {
            "stock": 50
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ── STOCK FAIBLE ───────────────────────

    def test_stock_faible(self):
        self.produit.stock = 1
        self.produit.save()

        self.assertTrue(self.produit.stock_faible)