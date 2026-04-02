from rest_framework import serializers
from clients.models import Client


# ── Mixin — validations réutilisables ────────
class ClientValidationMixin:

    def validate_cin(self, value):
        if len(value) != 8:
            raise serializers.ValidationError(
                "Le CIN doit contenir 8 chiffres"
            )
        return value

    def validate_telephone_1(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(
                "Le numéro doit contenir au moins 8 chiffres"
            )
        return value


# ── Serializer liste et détail ───────────────
class ClientSerializer(ClientValidationMixin, serializers.ModelSerializer):

    abonnement_actif = serializers.SerializerMethodField()

    class Meta:
        model  = Client
        fields = [
            'id',
            'nom',
            'prenom',
            'cin',
            'telephone_1',
            'telephone_2',
            'email',
            'date_naissance',
            'photo',
            'essai_fait',
            'statut',
            'abonnement_actif',
            'created_at',
        ]
        read_only_fields = ['essai_fait', 'statut', 'created_at']

    def get_abonnement_actif(self, obj):
        abo = obj.abonnement_actif
        if not abo:
            return 'inactif'

        if not abo.pack:
            return 'sans pack'

        return abo.pack.nom


# ── Serializer création ──────────────────────
class CreerClientSerializer(ClientValidationMixin, serializers.Serializer):
    nom            = serializers.CharField(max_length=100)
    prenom         = serializers.CharField(max_length=100)
    cin            = serializers.CharField(max_length=20)
    telephone_1    = serializers.CharField(max_length=20,allow_blank=True)
    telephone_2    = serializers.CharField(max_length=20,  required=False, default='')
    email          = serializers.EmailField(required=False, default='')
    date_naissance = serializers.DateField(required=False,  allow_null=True, default=None)
    photo          = serializers.ImageField(required=False,  allow_null=True, default=None)

# ── Serializer modification ──────────────────
class ModifierClientSerializer(ClientValidationMixin, serializers.Serializer):

    nom            = serializers.CharField(max_length=100, required=False)
    prenom         = serializers.CharField(max_length=100, required=False)
    cin            = serializers.CharField(max_length=20,  required=False)
    telephone_1    = serializers.CharField(max_length=20,  required=False)
    telephone_2    = serializers.CharField(max_length=20,  required=False)
    email          = serializers.EmailField(required=False)
    date_naissance = serializers.DateField(required=False)
    photo          = serializers.ImageField(required=False)