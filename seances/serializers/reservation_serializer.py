from rest_framework import serializers
from seances.models import Reservation


class ReservationSerializer(serializers.ModelSerializer):

    client_nom   = serializers.SerializerMethodField()
    client_cin   = serializers.SerializerMethodField()
    seance_info  = serializers.SerializerMethodField()
    type_label   = serializers.SerializerMethodField()
    statut_label = serializers.SerializerMethodField()

    class Meta:
        model  = Reservation
        fields = [
            'id',
            'abonnement',
            'client_nom',
            'seance',
            'client_cin',
            'seance_info',
            'personnel',
            'type_appareil',
            'taille_gilet',
            'type_label',
            'statut',
            'statut_label',
            'created_at',
            
        ]
        read_only_fields = ['statut', 'created_at']

    def get_client_nom(self, obj):
        c = obj.abonnement.client
        return f"{c.prenom} {c.nom}"

    def get_client_cin(self, obj):
        return obj.abonnement.client.cin

    def get_seance_info(self, obj):
        return f"{obj.seance.date} {obj.seance.heure_debut}"

    def get_type_label(self, obj):
        return obj.get_type_appareil_display()

    def get_statut_label(self, obj):
        return obj.get_statut_display()


class CreerReservationSerializer(serializers.Serializer):

    abonnement_id = serializers.UUIDField()
    seance_id     = serializers.UUIDField()
    type_appareil = serializers.ChoiceField(
                        choices=['i-motion', 'i-model']
                    )
    taille_gilet  = serializers.ChoiceField(
                        choices=[  'M', 'L', 'XL' ],
                        required=False
                    )

    def validate(self, data):
        from clients.models import Abonnement
        from seances.models import Seance

        # Vérifier abonnement
        try:
            abonnement = Abonnement.objects.get(id=data['abonnement_id'])
        except Abonnement.DoesNotExist:
            raise serializers.ValidationError("Abonnement non trouvé")

        # Vérifier abonnement actif ou en_attente
        if abonnement.statut not in ['actif', 'en_attente']:
            raise serializers.ValidationError(
                "Cet abonnement est terminé ou expiré"
            )

        # Vérifier séances restantes
        if abonnement.seances_restantes <= 0:
            raise serializers.ValidationError(
                "Plus de séances disponibles"
            )

        # Vérifier créneau
        try:
            seance = Seance.objects.get(id=data['seance_id'])
        except Seance.DoesNotExist:
            raise serializers.ValidationError("Créneau non trouvé")

        # Vérifier places disponibles
        if not seance.est_disponible:
            raise serializers.ValidationError("Ce créneau est complet")

        data['abonnement'] = abonnement
        data['seance']     = seance
        return data
    
class CreerReservationSwaggerSerializer(serializers.Serializer):
    abonnement_id = serializers.UUIDField()
    type_appareil = serializers.ChoiceField(choices=['i-motion', 'i-model'])
    taille_gilet  = serializers.ChoiceField(choices=[ 'M', 'L', 'XL' ], required=False)