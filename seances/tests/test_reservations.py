from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import Utilisateur
from clients.models import Client, Abonnement, Pack
from seances.models import Seance
from datetime import date, time


class ReservationTestCase(TestCase):

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

        # Token admin
        login = self.client_api.post('/api/users/login/', {
            'username': 'admin_test',
            'password': 'admin1234'
        })
        self.token = login.data['access']
        self.client_api.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )

        # Créer client
        self.client_test = Client.objects.create(
            nom         = 'Ben Ali',
            prenom      = 'Mohamed',
            cin         = '12345678',
            telephone_1 = '55123456',
        )

        # Créer abonnement pack10
        self.pack_test = Pack.objects.create(nom='Pack 10', nb_seances=10, prix=350, est_actif=True)
        self.abonnement = Abonnement.objects.create(
            client            = self.client_test,
            pack              = self.pack_test,
            statut            = 'actif',
            seances_restantes = 10,
            prix_paye         = 350,
            mode_paiement     = 'cash',
            est_paye          = True,
        )

        # Créer créneau
        self.seance = Seance.objects.create(
            date               = date.today(),
            heure_debut        = time(9, 0),
            heure_fin          = time(9, 30),
            places_total       = 3,
            places_disponibles = 3,
        )

        self.url_reservations = f'/api/seances/{self.seance.id}/reservations/'

    # ── Tests créer réservation ──────────────

    def test_creer_reservation_correct(self):
        response = self.client_api.post(self.url_reservations, {
            'abonnement_id': str(self.abonnement.id),
            'type_appareil': 'i-motion',
            'taille_gilet': 'M',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['statut'], 'en_attente')
        self.assertEqual(response.data['type_appareil'], 'i-motion')
        self.assertEqual(response.data['taille_gilet'], 'M')

    def test_places_decrementees_apres_reservation(self):
        self.client_api.post(self.url_reservations, {
            'abonnement_id': str(self.abonnement.id),
            'type_appareil': 'i-motion',
            'taille_gilet': 'M',
        })
        self.seance.refresh_from_db()
        self.assertEqual(self.seance.places_disponibles, 2)

    def test_double_reservation_meme_creneau_refuse(self):
        # Première réservation
        self.client_api.post(self.url_reservations, {
            'abonnement_id': str(self.abonnement.id),
            'type_appareil': 'i-motion',
            'taille_gilet': 'M',
        })
        # Deuxième réservation dans le même créneau
        response = self.client_api.post(self.url_reservations, {
            'abonnement_id': str(self.abonnement.id),
            'type_appareil': 'i-model',
            'taille_gilet': 'M',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_reservation_creneau_complet_refuse(self):
        # Remplir le créneau
        self.seance.places_disponibles = 0
        self.seance.save()

        response = self.client_api.post(self.url_reservations, {
            'abonnement_id': str(self.abonnement.id),
            'type_appareil': 'i-motion',
            'taille_gilet': 'M',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reservation_abonnement_sans_seances_refuse(self):
        self.abonnement.seances_restantes = 0
        self.abonnement.save()

        response = self.client_api.post(self.url_reservations, {
            'abonnement_id': str(self.abonnement.id),
            'type_appareil': 'i-motion',
            'taille_gilet': 'M',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ── Tests marquer présent ────────────────

    def test_marquer_present_correct(self):
        # Créer réservation
        res = self.client_api.post(self.url_reservations, {
            'abonnement_id': str(self.abonnement.id),
            'type_appareil': 'i-motion',
            'taille_gilet': 'M',
        })
        reservation_id = res.data['id']

        # Marquer présent
        response = self.client_api.patch(
            f'/api/seances/reservations/{reservation_id}/present/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['statut'], 'present')

    def test_seances_decrementees_apres_present(self):
        # Créer réservation
        res = self.client_api.post(self.url_reservations, {
            'abonnement_id': str(self.abonnement.id),
            'type_appareil': 'i-motion',
            'taille_gilet': 'M',
        })
        reservation_id = res.data['id']

        # Marquer présent
        self.client_api.patch(
            f'/api/seances/reservations/{reservation_id}/present/'
        )
        self.abonnement.refresh_from_db()
        self.assertEqual(self.abonnement.seances_restantes, 9)

    def test_marquer_present_deux_fois_refuse(self):
        res = self.client_api.post(self.url_reservations, {
            'abonnement_id': str(self.abonnement.id),
            'type_appareil': 'i-motion',
            'taille_gilet': 'M',
        })
        reservation_id = res.data['id']

        self.client_api.patch(
            f'/api/seances/reservations/{reservation_id}/present/'
        )
        response = self.client_api.patch(
            f'/api/seances/reservations/{reservation_id}/present/'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ── Tests marquer absent ─────────────────

    def test_marquer_absent_correct(self):
        res = self.client_api.post(self.url_reservations, {
            'abonnement_id': str(self.abonnement.id),
            'type_appareil': 'i-motion',
            'taille_gilet': 'M',
        })
        reservation_id = res.data['id']

        response = self.client_api.patch(
            f'/api/seances/reservations/{reservation_id}/absent/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['statut'], 'absent')

    def test_place_liberee_apres_absent(self):
        res = self.client_api.post(self.url_reservations, {
            'abonnement_id': str(self.abonnement.id),
            'type_appareil': 'i-motion',
            'taille_gilet': 'M',
        })
        reservation_id = res.data['id']

        self.client_api.patch(
            f'/api/seances/reservations/{reservation_id}/absent/'
        )
        self.seance.refresh_from_db()
        self.assertEqual(self.seance.places_disponibles, 3)

    def test_seances_non_decrementees_apres_absent(self):
        res = self.client_api.post(self.url_reservations, {
            'abonnement_id': str(self.abonnement.id),
            'type_appareil': 'i-motion',
            'taille_gilet': 'M',
        })
        reservation_id = res.data['id']

        self.client_api.patch(
            f'/api/seances/reservations/{reservation_id}/absent/'
        )
        self.abonnement.refresh_from_db()
        self.assertEqual(self.abonnement.seances_restantes, 10)

    # ── Tests annuler ────────────────────────

    def test_annuler_reservation_correct(self):
        res = self.client_api.post(self.url_reservations, {
            'abonnement_id': str(self.abonnement.id),
            'type_appareil': 'i-motion',
            'taille_gilet': 'M',
        })
        reservation_id = res.data['id']

        response = self.client_api.patch(
            f'/api/seances/reservations/{reservation_id}/annuler/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['statut'], 'annule')

    def test_place_liberee_apres_annulation(self):
        res = self.client_api.post(self.url_reservations, {
            'abonnement_id': str(self.abonnement.id),
            'type_appareil': 'i-motion',
            'taille_gilet': 'M',
        })
        reservation_id = res.data['id']

        self.client_api.patch(
            f'/api/seances/reservations/{reservation_id}/annuler/'
        )
        self.seance.refresh_from_db()
        self.assertEqual(self.seance.places_disponibles, 3)

    # ── Tests plusieurs réservations ─────────

    def test_cinq_reservations_different_clients(self):
        # Créer 5 clients avec abonnements
        for i in range(1, 4):
            client = Client.objects.create(
                nom         = f'Client{i}',
                prenom      = 'Test',
                cin         = f'1234567{i}',
                telephone_1 = f'5512345{i}',
            )
            abo = Abonnement.objects.create(
                client            = client,
                pack              = self.pack_test,
                statut            = 'actif',
                seances_restantes = 10,
                prix_paye         = 350,
                mode_paiement     = 'cash',
                est_paye          = True,
            )
            response = self.client_api.post(self.url_reservations, {
                'abonnement_id': str(abo.id),
                'type_appareil': 'i-motion',
                'taille_gilet': 'M',
            })
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.seance.refresh_from_db()
        self.assertEqual(self.seance.places_disponibles, 0)

    def test_sixieme_reservation_refuse_creneau_complet(self):
        # Remplir avec 3 clients
        for i in range(1, 4):
            client = Client.objects.create(
                nom         = f'Client{i}',
                prenom      = 'Test',
                cin         = f'1234567{i}',
                telephone_1 = f'5512345{i}',
            )
            abo = Abonnement.objects.create(
                client            = client,
                pack              = self.pack_test,
                statut            = 'actif',
                seances_restantes = 10,
                prix_paye         = 350,
                mode_paiement     = 'cash',
                est_paye          = True,
            )
            self.client_api.post(self.url_reservations, {
                'abonnement_id': str(abo.id),
                'type_appareil': 'i-motion',
                'taille_gilet': 'M',
            })

        # 6ème réservation doit être refusée
        response = self.client_api.post(self.url_reservations, {
            'abonnement_id': str(self.abonnement.id),
            'type_appareil': 'i-motion',
            'taille_gilet': 'M',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_creer_reservation_sans_taille_ok(self):
        # POST sans taille_gilet doit réussir
        response = self.client_api.post(self.url_reservations, {
            'abonnement_id': str(self.abonnement.id),
            'type_appareil': 'i-motion',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data.get('taille_gilet'))

    def test_creer_reservation_taille_invalide(self):
        # Taille invalide doit retourner 400
        response = self.client_api.post(self.url_reservations, {
            'abonnement_id': str(self.abonnement.id),
            'type_appareil': 'i-motion',
            'taille_gilet': 'XXL',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)