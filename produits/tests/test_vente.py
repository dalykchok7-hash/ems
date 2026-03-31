from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import Utilisateur
from produits.models import Produit, Vente


class VenteTestCase(TestCase):

    def setUp(self):
        self.client_api = APIClient()

        # ── User ─────────────────────────────
        self.user = Utilisateur.objects.create_user(
            username='pers_test',
            password='pers1234',
            email='pers@test.com',
            cin='88888888',
            role='personnel',
        )

        login = self.client_api.post('/api/users/login/', {
            'username': 'pers_test',
            'password': 'pers1234'
        })
        self.token = login.data['access']

        # ── Produits ─────────────────────────
        self.produit1 = Produit.objects.create(
            nom="Whey",
            type="complement",
            prix_unitaire=100,
            stock=10
        )

        self.produit2 = Produit.objects.create(
            nom="Creatine",
            type="complement",
            prix_unitaire=50,
            stock=5
        )

    # ── CREER VENTE ────────────────────────

    def test_creer_vente_valide(self):
        self.client_api.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        response = self.client_api.post('/api/produits/ventes/', {
            "lignes": [
                {"produit_id": str(self.produit1.id), "quantite": 2},
                {"produit_id": str(self.produit2.id), "quantite": 1}
            ]
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        vente = Vente.objects.first()
        self.assertEqual(float(vente.prix_total), 250)

    # ── STOCK DIMINUE ──────────────────────

    def test_stock_diminue_apres_vente(self):
        self.client_api.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        self.client_api.post('/api/produits/ventes/', {
            "lignes": [
                {"produit_id": str(self.produit1.id), "quantite": 2}
            ]
        }, format='json')

        self.produit1.refresh_from_db()
        self.assertEqual(self.produit1.stock, 8)

    # ── STOCK INSUFFISANT ──────────────────

    def test_stock_insuffisant(self):
        self.client_api.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        response = self.client_api.post('/api/produits/ventes/', {
            "lignes": [
                {"produit_id": str(self.produit2.id), "quantite": 999}
            ]
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ── VENTE VIDE ─────────────────────────

    def test_vente_sans_lignes(self):
        self.client_api.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        response = self.client_api.post('/api/produits/ventes/', {
            "lignes": []
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ── HISTORIQUE ─────────────────────────

    def test_historique_ventes(self):
        self.client_api.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        response = self.client_api.get('/api/produits/ventes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)