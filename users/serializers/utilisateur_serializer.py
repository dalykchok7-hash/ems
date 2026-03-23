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
    first_name    = serializers.CharField(max_length=100)
    last_name     = serializers.CharField(max_length=100)
    cin           = serializers.CharField(max_length=20)
    telephone     = serializers.CharField(max_length=20, required=False, default='')
    shift         = serializers.ChoiceField(choices=['jour', 'soir'])
    date_embauche = serializers.DateField()

    def validate_cin(self, value):
        if len(value) != 8:
            raise serializers.ValidationError(
                "Le CIN doit contenir 8 chiffres"
            )
        return value


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128, write_only=True)
    
class ModifierPersonnelSerializer(serializers.Serializer):
    first_name    = serializers.CharField(max_length=100, required=False)
    last_name     = serializers.CharField(max_length=100, required=False)
    telephone     = serializers.CharField(max_length=20,  required=False)
    shift         = serializers.ChoiceField(
                        choices  = ['jour', 'soir'],
                        required = False
                    )
    date_embauche = serializers.DateField(required=False)