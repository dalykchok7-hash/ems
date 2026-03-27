from rest_framework import serializers
from clients.models import Abonnement


class AbonnementSerializer(serializers.ModelSerializer):

    client_nom = serializers.SerializerMethodField()
    type_label = serializers.SerializerMethodField()

    class Meta:
        model  = Abonnement
        fields = [
            'id',
            'client',
            'client_nom',
            'type',
            'type_label',
            'reduction',
            'prix_paye',
            'mode_paiement',
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
            'client',
            'prix_paye',
            'seances_total',
            'seances_restantes',
            'date_debut',
            'statut',
            'created_at',
        ]

    def get_client_nom(self, obj):
        return f"{obj.client.prenom} {obj.client.nom}"

    def get_type_label(self, obj):
        return obj.get_type_display()


class CreerAbonnementSerializer(serializers.Serializer):

    type          = serializers.ChoiceField(
                        choices=['essai','unique', 'pack5', 'pack10', 'pack20','pack30']
                    )
    mode_paiement = serializers.ChoiceField(
                        choices=['cash', 'tpe'],
                        required=False,
                        default=''
                    )
    est_paye      = serializers.BooleanField(default=False)
    date_paiement = serializers.DateField(required=False, allow_null=True)
    date_expiration = serializers.DateField(required=False, allow_null=True)
    reduction     = serializers.DecimalField(
                        max_digits=5,
                        decimal_places=2,
                        required=False,
                        default=0
                    )

    def validate_reduction(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "La réduction doit être entre 0 et 100"
            )
        return value


class ModifierAbonnementSerializer(serializers.Serializer):

    mode_paiement   = serializers.ChoiceField(
                          choices=['cash', 'tpe'],
                          required=False
                      )
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
            raise serializers.ValidationError(
                "La réduction doit être entre 0 et 100"
            )
        return value