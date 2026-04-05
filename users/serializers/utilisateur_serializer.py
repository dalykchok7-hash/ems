from rest_framework import serializers
from users.models import Utilisateur


class UtilisateurSerializer(serializers.ModelSerializer):

    class Meta:
        model  = Utilisateur
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'email',   
            'cin',
            'telephone',
            'role',
            'shift',
            'date_embauche',
            'photo',
            'is_active',
            'date_joined',
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }


class CreerPersonnelSerializer(serializers.Serializer):

    username      = serializers.CharField(max_length=150)
    password      = serializers.CharField(max_length=128, write_only=True)
    email         = serializers.EmailField(required=True)
    first_name    = serializers.CharField(max_length=100)
    last_name     = serializers.CharField(max_length=100)
    cin           = serializers.CharField(max_length=20)
    telephone     = serializers.CharField(max_length=20, required=False, default='')
    shift         = serializers.ChoiceField(choices=['jour', 'soir'])
    date_embauche = serializers.DateField()

    def validate_email(self, value):
        if Utilisateur.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value

    def validate_username(self, value):
        if Utilisateur.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return value

    def validate_cin(self, value):
        if len(value) != 8:
            raise serializers.ValidationError("Le CIN doit contenir 8 chiffres.")
        if Utilisateur.objects.filter(cin__iexact=value).exists():
            raise serializers.ValidationError("Ce CIN est déjà utilisé.")
        return value


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128, write_only=True)

class ModifierPersonnelSerializer(serializers.Serializer):
    first_name    = serializers.CharField(max_length=100, required=False)
    last_name     = serializers.CharField(max_length=100, required=False)
    email         = serializers.EmailField(required=False)        # ← ajouter
    cin           = serializers.CharField(max_length=8, required=False)   # ← ajouter
    telephone     = serializers.CharField(max_length=20, required=False)
    shift         = serializers.ChoiceField(choices=['jour', 'soir'], required=False)
    date_embauche = serializers.DateField(required=False)
class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=6)