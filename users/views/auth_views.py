from historique.services.historique_service import HistoriqueService
from rest_framework.views    import APIView
from rest_framework.response import Response
from rest_framework          import status
from rest_framework.permissions import AllowAny

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

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
        try:
            resultat = AuthService.login(
                username = request.data.get('username'),
                password = request.data.get('password'),
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )
        try:
            from users.models import Utilisateur
            personnel = Utilisateur.objects.get(
                username=request.data.get('username')
            )
            HistoriqueService.connexion(personnel)
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