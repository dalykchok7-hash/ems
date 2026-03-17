from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from produits.models import Vente, LigneVente, Produit


class LigneVenteSerializer(serializers.ModelSerializer):

    produit_nom   = serializers.SerializerMethodField()
    prix_unitaire = serializers.SerializerMethodField()

    class Meta:
        model  = LigneVente
        fields = [
            'id',
            'produit',
            'produit_nom',
            'quantite',
            'prix_unitaire',
            'prix_total',
        ]

    @extend_schema_field(OpenApiTypes.STR)
    def get_produit_nom(self, obj):
        return obj.produit.nom

    @extend_schema_field(OpenApiTypes.DECIMAL)
    def get_prix_unitaire(self, obj):
        return obj.prix_unitaire


class VenteSerializer(serializers.ModelSerializer):

    lignes        = LigneVenteSerializer(many=True, read_only=True)
    personnel_nom = serializers.SerializerMethodField()

    class Meta:
        model  = Vente
        fields = [
            'id',
            'personnel',
            'personnel_nom',
            'lignes',
            'prix_total',
            'created_at',
        ]
        read_only_fields = ['prix_total', 'created_at']

    @extend_schema_field(OpenApiTypes.STR)
    def get_personnel_nom(self, obj):
        return obj.personnel.get_full_name() or obj.personnel.username


class LigneVenteInputSerializer(serializers.Serializer):
    produit_id = serializers.UUIDField()
    quantite   = serializers.IntegerField(min_value=1)


class CreerVenteSerializer(serializers.Serializer):

    lignes = LigneVenteInputSerializer(many=True)

    def validate_lignes(self, lignes):
        if not lignes:
            raise serializers.ValidationError(
                "La vente doit contenir au moins un produit"
            )

        for ligne in lignes:
            try:
                produit = Produit.objects.get(
                    id        = ligne['produit_id'],
                    est_actif = True
                )
            except Produit.DoesNotExist:
                raise serializers.ValidationError(
                    f"Produit {ligne['produit_id']} non trouvé"
                )

            if produit.stock < ligne['quantite']:
                raise serializers.ValidationError(
                    f"Stock insuffisant pour {produit.nom}. "
                    f"Disponible: {produit.stock}"
                )

            ligne['produit'] = produit

        return lignes