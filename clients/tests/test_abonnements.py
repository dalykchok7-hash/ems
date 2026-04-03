from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import Utilisateur
from clients.models import Client, Abonnement, Pack
from datetime import date, timedelta


class PackTestCase(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.admin = Utilisateur.objects.create_superuser(
            username='admin_pack', password='123', cin='11112222', email='pack@test.com', role='admin'
        )
        login = self.client_api.post('/api/users/login/', {'username': 'admin_pack', 'password': '123'})
        self.token = login.data['access']
        self.client_api.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_creer_pack(self):
        response = self.client_api.post('/api/clients/packs/', {
            'nom': 'Pack Gold',
            'nb_seances': 20,
            'prix': 500,
            'description': 'Description du pack test'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nom'], 'Pack Gold')
        self.assertEqual(float(response.data['prix']), 500.0)

    def test_creer_pack_prix_negatif_refuse(self):
        response = self.client_api.post('/api/clients/packs/', {
            'nom': 'Pack Négatif',
            'nb_seances': 10,
            'prix': -50
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_modifier_pack(self):
        pack = Pack.objects.create(nom='Pack Normal', nb_seances=10, prix=100)
        response = self.client_api.put(f'/api/clients/packs/{pack.id}/', {
            'nom': 'Pack Modifié',
            'prix': 150
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nom'], 'Pack Modifié')
        self.assertEqual(float(response.data['prix']), 150.0)

    def test_desactiver_pack(self):
        pack = Pack.objects.create(nom='Pack à désactiver', nb_seances=5, prix=50)
        response = self.client_api.delete(f'/api/clients/packs/{pack.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pack.refresh_from_db()
        self.assertFalse(pack.est_actif)


class AbonnementTestCase(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.admin = Utilisateur.objects.create_superuser(
            username='admin_abo', password='123', cin='33334444', email='abo@test.com', role='admin'
        )
        login = self.client_api.post('/api/users/login/', {'username': 'admin_abo', 'password': '123'})
        self.token = login.data['access']
        self.client_api.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        self.client_test = Client.objects.create(
            nom='NomTest', prenom='PrenomTest', cin='55556666', telephone_1='01020304'
        )
        self.pack_test = Pack.objects.create(
            nom='Pack 10', nb_seances=10, prix=200
        )

    def test_creer_abonnement_normal(self):
        response = self.client_api.post(f'/api/clients/{self.client_test.cin}/abonnement/', {
            'pack_id': str(self.pack_test.id),
            'mode_paiement': 'cash',
            'est_paye': True,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(float(response.data['prix_paye']), 200.0)
        self.assertEqual(response.data['seances_restantes'], 10)

    def test_creer_abonnement_avec_reduction(self):
        response = self.client_api.post(f'/api/clients/{self.client_test.cin}/abonnement/', {
            'pack_id': str(self.pack_test.id),
            'mode_paiement': 'cash',
            'reduction': 10  # 10% de réduction sur 200 = 180
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(float(response.data['prix_paye']), 180.0)

    def test_creer_abonnement_reduction_invalide(self):
        response = self.client_api.post(f'/api/clients/{self.client_test.cin}/abonnement/', {
            'pack_id': str(self.pack_test.id),
            'reduction': 150  # Max 100
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_double_abonnement_actif_refuse(self):
        # Créer le premier abonnement actif
        Abonnement.objects.create(
            client=self.client_test, pack=self.pack_test, statut='actif',
            seances_total=10, seances_restantes=10, prix_paye=200
        )
        
        # Tenter d'ajouter un autre
        response = self.client_api.post(f'/api/clients/{self.client_test.cin}/abonnement/', {
            'pack_id': str(self.pack_test.id)
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_obtenir_abonnement_actif(self):
        abo = Abonnement.objects.create(
            client=self.client_test, pack=self.pack_test, statut='actif',
            seances_total=10, seances_restantes=10, prix_paye=200
        )
        response = self.client_api.get(f'/api/clients/{self.client_test.cin}/abonnement/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(abo.id))
        self.assertEqual(response.data['seances_utilisees'], 0)

    def test_obtenir_abonnement_aucun_actif(self):
        # Abonnement expiré
        Abonnement.objects.create(
            client=self.client_test, pack=self.pack_test, statut='expire',
            seances_total=10, seances_restantes=0, prix_paye=200
        )
        response = self.client_api.get(f'/api/clients/{self.client_test.cin}/abonnement/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Retourne un mapping vide
        self.assertIsNone(response.data['id'])

    def test_liste_tous_abonnements(self):
        Abonnement.objects.create(
            client=self.client_test, pack=self.pack_test, statut='actif',
            seances_total=10, seances_restantes=10, prix_paye=200
        )
        response = self.client_api.get('/api/clients/abonnements/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_modifier_abonnement(self):
        abo = Abonnement.objects.create(
            client=self.client_test, pack=self.pack_test, statut='actif',
            seances_total=10, seances_restantes=10, prix_paye=200, est_paye=False
        )
        response = self.client_api.put(f'/api/clients/abonnements/{abo.id}/', {
            'est_paye': True,
            'mode_paiement': 'tpe'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['est_paye'])
        self.assertEqual(response.data['mode_paiement'], 'tpe')
