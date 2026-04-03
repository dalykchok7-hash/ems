from rest_framework.views       import APIView
from rest_framework.response    import Response
from rest_framework             import status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from users.models import Utilisateur
from drf_spectacular.utils import extend_schema,  OpenApiExample
from drf_spectacular.types import OpenApiTypes


from rest_framework_simplejwt.tokens     import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.utils.crypto import get_random_string
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
        summary="Modifier email admin",
        request=OpenApiTypes.OBJECT,
        responses={200: OpenApiTypes.OBJECT},
        examples=[
            OpenApiExample(
                "Requête",
                value={"email": "chihajihed3@gmail.com"},
                request_only=True,
            ),
            OpenApiExample(
                "Succès",
                value={"message": "Email modifié"},
                response_only=True,
            ),
        ],
    )
    def post(self, request):
        

        email = request.data.get("email")

        if not email:
            return Response({"error": "Email requis"}, status=400)

        try:
            admin = Utilisateur.objects.get(id=request.user.id)

            admin.email = email
            admin.save()

            return Response({
                "message": "Email modifié",
                "email": admin.email
            })

        except Utilisateur.DoesNotExist:
            return Response({"error": "Admin non trouvé"}, status=404)

class ResetPasswordView(APIView):

    def post(self, request):
        token = request.data.get("token")
        new_password = request.data.get("password")

        if not token or not new_password:
            return Response({"error": "Token et password requis"}, status=400)

        user = Utilisateur.objects.filter(reset_token=token).first()

        if not user:
            return Response({"error": "Token invalide"}, status=400)

        # changer password
        user.set_password(new_password)

        # supprimer token après usage
        user.reset_token = None
        user.save()

        return Response({
            "message": "Mot de passe mis à jour avec succès"
        })
class ForgotPasswordView(APIView):

    def post(self, request):
        email = request.data.get("email")

        user = Utilisateur.objects.filter(email__iexact=email).first()

        if not user:
            return Response({
                "message": "Si cet email existe, un lien de réinitialisation sera envoyé"
            })

        # Générer un token simple
        token = get_random_string(50)

        # Sauvegarder token dans le user (ou table dédiée)
        user.reset_token = token
        user.save()

        # Ici normalement tu envoies un email avec le lien
        reset_link = f"https://ton-frontend/reset-password?token={token}"

        return Response({
            "message": "Lien de réinitialisation généré",
            "reset_link": reset_link
        })