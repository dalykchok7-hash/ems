from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import Utilisateur


class LoginTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url    = '/api/users/login/'

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
            cin      = '12345678',
            role     = 'personnel',
        )

    def test_login_admin_correct(self):
        response = self.client.post(self.url, {
            'username': 'admin_test',
            'password': 'admin1234'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access',  response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['role'], 'admin')

    def test_login_personnel_correct(self):
        response = self.client.post(self.url, {
            'username': 'karim_test',
            'password': 'karim1234'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertEqual(response.data['user']['role'], 'personnel')

    def test_login_mauvais_password(self):
        response = self.client.post(self.url, {
            'username': 'admin_test',
            'password': 'mauvais_password'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    def test_login_mauvais_username(self):
        response = self.client.post(self.url, {
            'username': 'utilisateur_inexistant',
            'password': 'admin1234'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_champs_vides(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_username_vide(self):
        response = self.client.post(self.url, {
            'username': '',
            'password': 'admin1234'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_compte_desactive(self):
        self.admin.is_active = False
        self.admin.save()
        response = self.client.post(self.url, {
            'username': 'admin_test',
            'password': 'admin1234'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CreerPersonnelTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url    = '/api/users/'

        # Créer admin
        self.admin = Utilisateur.objects.create_superuser(
            username = 'admin_test',
            password = 'admin1234',
            email    = 'admin@test.com',
            cin      = '99999999',
            role     = 'admin',
        )

        # Créer personnel existant
        self.personnel = Utilisateur.objects.create_user(
            username = 'karim_test',
            password = 'karim1234',
            email    = 'karim@test.com',
            cin      = '12345678',
            role     = 'personnel',
        )

        # Token admin
        login = self.client.post('/api/users/login/', {
            'username': 'admin_test',
            'password': 'admin1234'
        })
        self.token_admin = login.data['access']

        # Token personnel
        login2 = self.client.post('/api/users/login/', {
            'username': 'karim_test',
            'password': 'karim1234'
        })
        self.token_personnel = login2.data['access']

    def test_creer_personnel_par_admin(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.token_admin}'
        )
        response = self.client.post(self.url, {
            'username'     : 'nouveau_personnel',
            'password'     : 'pass1234',
            'first_name'   : 'Nouveau',
            'last_name'    : 'Personnel',
            'cin'          : '11111111',
            'shift'        : 'jour',
            'date_embauche': '2026-01-01',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_creer_personnel_par_personnel_refuse(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.token_personnel}'
        )
        response = self.client.post(self.url, {
            'username'     : 'nouveau_personnel',
            'password'     : 'pass1234',
            'first_name'   : 'Nouveau',
            'last_name'    : 'Personnel',
            'cin'          : '22222222',
            'shift'        : 'jour',
            'date_embauche': '2026-01-01',
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_creer_personnel_sans_token_refuse(self):
        self.client.credentials()
        response = self.client.post(self.url, {
            'username'     : 'nouveau_personnel',
            'password'     : 'pass1234',
            'first_name'   : 'Nouveau',
            'last_name'    : 'Personnel',
            'cin'          : '33333333',
            'shift'        : 'jour',
            'date_embauche': '2026-01-01',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_creer_personnel_cin_duplique(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.token_admin}'
        )
        response = self.client.post(self.url, {
            'username'     : 'autre_personnel',
            'password'     : 'pass1234',
            'first_name'   : 'Autre',
            'last_name'    : 'Personnel',
            'cin'          : '12345678',  # ← CIN déjà utilisé
            'shift'        : 'jour',
            'date_embauche': '2026-01-01',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_creer_personnel_champs_manquants(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.token_admin}'
        )
        response = self.client.post(self.url, {
            'username': 'personnel_incomplet',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_creer_personnel_cin_invalide(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.token_admin}'
        )
        response = self.client.post(self.url, {
            'username'     : 'personnel_cin',
            'password'     : 'pass1234',
            'first_name'   : 'Test',
            'last_name'    : 'CIN',
            'cin'          : '123',  # ← CIN trop court
            'shift'        : 'jour',
            'date_embauche': '2026-01-01',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)