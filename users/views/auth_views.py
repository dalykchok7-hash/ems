from rest_framework.views       import APIView
from rest_framework.response    import Response
from rest_framework             import status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from users.models import Utilisateur
from drf_spectacular.utils import extend_schema,  OpenApiExample
from drf_spectacular.types import OpenApiTypes


from rest_framework_simplejwt.tokens     import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from users.serializers   import LoginSerializer,LogoutSerializer
from users.services      import AuthService

from historique.services import HistoriqueService


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary   = 'Connexion',
        request   = LoginSerializer,
        responses = {
            200: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_401_UNAUTHORIZED
            )

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

    # ✅ Historique (sans casser l'app)
        try:
            HistoriqueService.connexion(resultat.get('instance'))
        except Exception:
            pass

    # ❗ IMPORTANT → ne pas renvoyer "instance" au frontend
        resultat.pop('instance', None)

        return Response(resultat, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary   = 'Déconnexion',
        request   = LogoutSerializer,
        responses = {
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
        try:
            HistoriqueService.deconnexion(request.user)
        except Exception:
            pass

        return Response(
            {'message': 'Déconnexion réussie'},
            status=status.HTTP_200_OK
        )
class UpdateAdminEmailView(APIView):
    permission_classes = []  # temporaire

    @extend_schema(
        summary="Modifier email admin (temporaire)",
        description="Met à jour l'email de l'utilisateur admin",
        responses={
            200: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "Succès",
                value={"message": "Email modifié"},
                response_only=True,
            ),
            OpenApiExample(
                "Erreur",
                value={"error": "Admin non trouvé"},
                response_only=True,
            ),
        ],
    )
    def get(self, request):
        

        admin = Utilisateur.objects.get(username="admin")
        admin.email = "chihajihed3@gmail.com"
        admin.save()

        return Response({"message": "Email modifié"})