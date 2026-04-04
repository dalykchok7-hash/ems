import os
from rest_framework.views       import APIView
from rest_framework.response    import Response
from rest_framework             import status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from users.models import Utilisateur
from drf_spectacular.utils import extend_schema,  OpenApiExample
from drf_spectacular.types import OpenApiTypes
from django.core.mail import send_mail
from django.conf import settings

from rest_framework_simplejwt.tokens     import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.utils.crypto import get_random_string
from users.serializers   import LoginSerializer, LogoutSerializer, ChangePasswordSerializer
from users.permissions   import IsAdmin
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
    permission_classes = [IsAdmin]
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

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Changer le mot de passe",
        description="Permet à un utilisateur connecté de modifier son mot de passe",
        request=ChangePasswordSerializer,
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "Exemple requête",
                value={
                    "old_password": "123456",
                    "new_password": "newpassword123"
                },
                request_only=True
            ),
            OpenApiExample(
                "Succès",
                value={"message": "Mot de passe modifié avec succès"},
                response_only=True
            ),
        ]
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            AuthService.change_password(
                user=request.user,
                old_password=serializer.validated_data['old_password'],
                new_password=serializer.validated_data['new_password']
            )

            return Response({"message": "Mot de passe modifié avec succès"})

        except ValueError as e:
            return Response({"error": str(e)}, status=400)

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        token        = request.data.get("token")
        new_password = request.data.get("new_password")  # ✅ correspond au frontend

        if not token or not new_password:
            return Response({"error": "Token et nouveau mot de passe requis"}, status=400)

        user = Utilisateur.objects.filter(reset_token=token).first()

        if not user:
            return Response({"error": "Token invalide ou expiré"}, status=400)

        # Changer le mot de passe
        user.set_password(new_password)

        # Invalider le token après usage
        user.reset_token = None
        user.save()

        return Response({
            "message": "Mot de passe mis à jour avec succès"
        })
class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")

        user = Utilisateur.objects.filter(email__iexact=email).first()
        print(user)
        if not user or user.role != 'admin':
            return Response({
                "message": "Cette fonctionalité n'est pas disponible pour votre compte."
            }, status=status.HTTP_400_BAD_REQUEST)

        token = get_random_string(6, allowed_chars='0123456789')
        user.reset_token = token
        user.save()

        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:4200')
        reset_link   = f"{frontend_url}/reset-password?token={token}"

        # ✅ ENVOI EMAIL
        try:
            send_mail(
                subject=f"[EMS] Code de récupération de compte : {token}",
                message=f"Votre code de sécurité EMS est : {token}\n\nLien de secours : {reset_link}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
                html_message=f"""
                <div style='font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; padding: 40px 20px; background-color: #f8fafc; color: #1e293b;'>
                    <div style='max-width: 600px; margin: 0 auto; background: white; padding: 32px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);'>
                        <h1 style='font-size: 24px; font-weight: 700; color: #0f172a; margin-bottom: 24px;'>Réinitialisation de mot de passe</h1>
                        <p style='font-size: 16px; line-height: 1.5; color: #475569;'>Bonjour,</p>
                        <p style='font-size: 16px; line-height: 1.5; color: #475569;'>Nous avons reçu une demande de réinitialisation pour votre compte <strong>EMS</strong>. Voici votre code de validation à usage unique :</p>
                        
                        <div style='margin: 32px 0; padding: 24px; background: #f1f5f9; text-align: center; border-radius: 8px;'>
                            <span style='font-family: monospace; font-size: 32px; font-weight: 800; color: #2563eb; letter-spacing: 8px;'>{token}</span>
                        </div>

                        <p style='font-size: 14px; line-height: 1.5; color: #64748b;'>Ce code expirera bientôt. Vous pouvez également cliquer sur le lien ci-dessous pour procéder directement :</p>
                        <div style='text-align: center; margin-top: 24px;'>
                            <a href='{reset_link}' style='display: inline-block; padding: 12px 24px; background-color: #2563eb; color: white; text-decoration: none; font-weight: 600; border-radius: 6px;'>Réinitialiser mon mot de passe</a>
                        </div>
                        
                        <hr style='margin-top: 40px; border: 0; border-top: 1px solid #e2e8f0;' />
                        <p style='font-size: 12px; color: #94a3b8; text-align: center; margin-top: 24px;'>
                            Si vous n'avez pas demandé cette action, vous pouvez ignorer cet email en toute sécurité.
                        </p>
                    </div>
                </div>
                """
            )
            print("EMAIL SENT SUCCESS")

        except Exception as e:
            import traceback
            traceback.print_exc()
            print("Erreur lors de l'envoi de l'email :", str(e))
            return Response({
                "error": "Échec de l'envoi de l'email",
                "details": str(e)
            }, status=500)

        return Response({
            "message": "Email envoyé avec succès"
        })

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Récupérer le profil",
        description="Retourne les informations de l'utilisateur connecté",
        responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request):
        user = request.user
        return Response({
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "nom": user.get_full_name(),
            "role": user.role
        })