from rest_framework import serializers
from clients.models import Abonnement, Pack


# ── Pack ─────────────────────────────────────────────────────────
class PackSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Pack
        fields = ['id', 'nom', 'nb_seances', 'prix', 'description', 'est_actif', 'created_at']


class CreerPackSerializer(serializers.Serializer):
    nom         = serializers.CharField(max_length=100)
    nb_seances  = serializers.IntegerField(min_value=1)
    prix        = serializers.DecimalField(max_digits=8, decimal_places=2)
    description = serializers.CharField(required=False, default='')

    def validate_prix(self, value):
        if value <= 0:
            raise serializers.ValidationError("Le prix doit être positif")
        return value


class ModifierPackSerializer(serializers.Serializer):
    nom         = serializers.CharField(max_length=100, required=False)
    nb_seances  = serializers.IntegerField(min_value=1, required=False)
    prix        = serializers.DecimalField(max_digits=8, decimal_places=2, required=False)
    description = serializers.CharField(required=False)
    est_actif   = serializers.BooleanField(required=False)

    def validate_prix(self, value):
        if value <= 0:
            raise serializers.ValidationError("Le prix doit être positif")
        return value


# ── Abonnement ───────────────────────────────────────────────────
class AbonnementSerializer(serializers.ModelSerializer):
    client_nom  = serializers.SerializerMethodField()
    pack_detail = PackSerializer(source='pack', read_only=True)

    class Meta:
        model  = Abonnement
        fields = [
            'id',
            'client',
            'client_nom',
            'pack',           # UUID du pack
            'pack_detail',    # objet pack complet (nom, nb_seances, prix)
            'reduction',      # % de réduction appliqué à cette transaction
            'prix_paye',      # prix final après réduction
            'mode_paiement',  # cash / tpe
            'est_paye',
            'date_paiement',
            'seances_total',
            'seances_restantes',
            'date_debut',
            'date_derniere_seance',
            'date_expiration',
            'statut',
            'created_at',
        ]
        read_only_fields = [
            'client', 'prix_paye',
            'seances_total', 'seances_restantes',
            'date_debut', 'statut', 'created_at',
        ]

    def get_client_nom(self, obj):
        return f"{obj.client.prenom} {obj.client.nom}"


class CreerAbonnementSerializer(serializers.Serializer):
    """
    Payload pour créer un abonnement.
    Le pack_id détermine le nombre de séances et le prix de base.
    La réduction, le mode de paiement et le statut de paiement
    sont propres à cette transaction.
    """
    pack_id         = serializers.UUIDField()
    mode_paiement   = serializers.ChoiceField(
                          choices=['cash', 'tpe'],
                          required=False,
                          default=''
                      )
    est_paye        = serializers.BooleanField(default=False)
    date_paiement   = serializers.DateField(required=False, allow_null=True)
    date_expiration = serializers.DateField(required=False, allow_null=True)
    reduction       = serializers.DecimalField(
                          max_digits=5,
                          decimal_places=2,
                          required=False,
                          default=0
                      )

    def validate_reduction(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("La réduction doit être entre 0 et 100")
        return value


class ModifierAbonnementSerializer(serializers.Serializer):
    """
    Payload pour modifier un abonnement existant.
    On peut modifier : paiement, réduction, dates.
    On ne peut PAS changer le pack après création.
    """
    mode_paiement   = serializers.ChoiceField(choices=['cash', 'tpe'], required=False)
    est_paye        = serializers.BooleanField(required=False)
    date_paiement   = serializers.DateField(required=False, allow_null=True)
    date_expiration = serializers.DateField(required=False, allow_null=True)
    reduction       = serializers.DecimalField(
                          max_digits=5,
                          decimal_places=2,
                          required=False
                      )

    def validate_reduction(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("La réduction doit être entre 0 et 100")
        return value