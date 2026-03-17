from rest_framework_simplejwt.tokens import RefreshToken
from users.models import Utilisateur
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.views    import APIView
from rest_framework.response import Response
from rest_framework          import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes
from rest_framework_simplejwt.tokens     import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from users.serializers   import UtilisateurSerializer, CreerPersonnelSerializer, LoginSerializer
from users.services      import AuthService
from users.permissions   import IsAdmin
from historique.services import HistoriqueService


class AuthService:

    @staticmethod
    def login(username, password):
        # Vérifier que l'utilisateur existe
        try:
            user = Utilisateur.objects.get(username=username)
        except Utilisateur.DoesNotExist:
            raise ValueError("Nom d'utilisateur incorrect")

        # Vérifier le mot de passe
        if not user.check_password(password):
            raise ValueError("Mot de passe incorrect")

        # Vérifier que le compte est actif
        if not user.is_active:
            raise ValueError("Ce compte est désactivé")

        # Générer les tokens
        refresh = RefreshToken.for_user(user)

        return {
            'access'  : str(refresh.access_token),
            'refresh' : str(refresh),
            'user'    : {
                'id'   : str(user.id),
                'role' : user.role,
            }
        }
    @staticmethod
    def creer_personnel(data):
        # Vérifier que le CIN n'existe pas déjà
        if Utilisateur.objects.filter(cin=data['cin']).exists():
            raise ValueError("Ce CIN existe déjà")

        # Vérifier que le username n'existe pas déjà
        if Utilisateur.objects.filter(username=data['username']).exists():
            raise ValueError("Ce nom d'utilisateur existe déjà")

        # Créer l'utilisateur
        user = Utilisateur.objects.create_user(
            username      = data['username'],
            password      = data['password'],
            first_name    = data['first_name'],
            last_name     = data['last_name'],
            cin           = data['cin'],
            telephone     = data.get('telephone', ''),
            role          = 'personnel',
            shift         = data['shift'],
            date_embauche = data['date_embauche'],
        )

        return user


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary     = 'Déconnexion',
        description = 'Invalide le refresh token',
        request     = None,
        responses   = {
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        }
    )
    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response(
                {'error': 'Refresh token manquant'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response(
                {'error': 'Token invalide'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Historique déconnexion
        try:
            HistoriqueService.deconnexion(request.user)
        except Exception:
            pass

        return Response(
            {'message': 'Déconnexion réussie'},
            status=status.HTTP_200_OK
        )