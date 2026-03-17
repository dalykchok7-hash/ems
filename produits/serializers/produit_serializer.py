from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from produits.models import Produit


class ProduitSerializer(serializers.ModelSerializer):

    stock_faible = serializers.ReadOnlyField()
    type_label   = serializers.SerializerMethodField()

    class Meta:
        model  = Produit
        fields = [
            'id',
            'nom',
            'type',
            'type_label',
            'prix_unitaire',
            'stock',
            'seuil_alerte',
            'stock_faible',
            'est_actif',
            'created_at',
        ]
        read_only_fields = ['created_at']

    @extend_schema_field(OpenApiTypes.STR)
    def get_type_label(self, obj):
        return obj.get_type_display()


class CreerProduitSerializer(serializers.Serializer):

    nom           = serializers.CharField(max_length=100)
    type          = serializers.ChoiceField(
                        choices=['complement', 'pre_workout', 'dose', 'autre']
                    )
    prix_unitaire = serializers.DecimalField(max_digits=8, decimal_places=2)
    stock         = serializers.IntegerField(min_value=0)
    seuil_alerte  = serializers.IntegerField(min_value=0, default=2)


class ModifierProduitSerializer(serializers.Serializer):

    nom           = serializers.CharField(max_length=100,  required=False)
    prix_unitaire = serializers.DecimalField(
                        max_digits=8, decimal_places=2, required=False
                    )
    stock         = serializers.IntegerField(min_value=0,  required=False)
    seuil_alerte  = serializers.IntegerField(min_value=0,  required=False)
    est_actif     = serializers.BooleanField(required=False)