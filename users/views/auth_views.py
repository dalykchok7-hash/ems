from historique.services.historique_service import HistoriqueService
from rest_framework.views    import APIView
from rest_framework.response import Response
from rest_framework          import status

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.permissions import AllowAny, IsAuthenticated
from users.serializers import UtilisateurSerializer, CreerPersonnelSerializer, LoginSerializer
from users.services    import AuthService
from users.permissions import IsAdmin


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary     = 'Connexion',
        description = 'Authentifie un utilisateur et retourne un token JWT',
        request     = LoginSerializer,
        responses   = {
            200: UtilisateurSerializer,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
        }
    )
    def post(self, request):
            serializer = LoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            try:
                resultat = AuthService.login(
                    username=username,
                    password=password,
            )
            except ValueError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_401_UNAUTHORIZED
            )
            try:
              HistoriqueService.connexion(resultat.get('instance'))
            except Exception:
                pass

            return Response(resultat, status=status.HTTP_200_OK)
       


class CreerPersonnelView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(
        summary     = 'Créer un membre du personnel',
        description = 'Crée un compte personnel. Réservé à l\'admin.',
        request     = CreerPersonnelSerializer,
        responses   = {
            201: UtilisateurSerializer,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
        }
    )
    def post(self, request):
       serializer = CreerPersonnelSerializer(data=request.data)
       if not serializer.is_valid():
         return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

       try:
          personnel = AuthService.creer_personnel(
            serializer.validated_data
        )
       except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

       return Response(
        UtilisateurSerializer(personnel).data,
        status=status.HTTP_201_CREATED
    )
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