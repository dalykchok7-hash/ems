from rest_framework import serializers
from seances.models import Seance


class SeanceSerializer(serializers.ModelSerializer):

    est_disponible     = serializers.ReadOnlyField()
    est_complet        = serializers.ReadOnlyField()
    reservations_count = serializers.SerializerMethodField()

    class Meta:
        model  = Seance
        fields = [
            'id',
            'date',
            'heure_debut',
            'heure_fin',
            'places_total',
            'places_disponibles',
            'est_disponible',
            'est_complet',
            'reservations_count',
            'created_at',
        ]
        read_only_fields = [
            'places_total',
            'places_disponibles',
            'created_at',
        ]

    def get_reservations_count(self, obj):
        return obj.reservations.filter(
            statut__in=['en_attente', 'present']
        ).count()