from rest_framework_simplejwt.tokens import RefreshToken
from users.models import Utilisateur


class AuthService:

    @staticmethod
    def login(username, password):
        try:
            user = Utilisateur.objects.get(username=username)
        except Utilisateur.DoesNotExist:
            raise ValueError("Nom d'utilisateur incorrect")

        if not user.check_password(password):
            raise ValueError("Mot de passe incorrect")

        if not user.is_active:
            raise ValueError("Ce compte est désactivé")

        refresh = RefreshToken.for_user(user)

        return {
            'access' : str(refresh.access_token),
            'refresh': str(refresh),
            'user'   : {
                'id'  : str(user.id),
                'role': user.role,
            }
        }

    @staticmethod
    def creer_personnel(data):
        if Utilisateur.objects.filter(cin=data['cin']).exists():
            raise ValueError("Ce CIN existe déjà")

        if Utilisateur.objects.filter(username=data['username']).exists():
            raise ValueError("Ce nom d'utilisateur existe déjà")

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