from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from historique.models import Historique


class HistoriqueSerializer(serializers.ModelSerializer):

    personnel_nom  = serializers.SerializerMethodField()
    action_label   = serializers.SerializerMethodField()

    class Meta:
        model  = Historique
        fields = [
            'id',
            'personnel',
            'personnel_nom',
            'action',
            'action_label',
            'details',
            'created_at',
        ]
        read_only_fields = fields

    @extend_schema_field(OpenApiTypes.STR)
    def get_personnel_nom(self, obj):
        return obj.personnel.get_full_name() or obj.personnel.username

    @extend_schema_field(OpenApiTypes.STR)
    def get_action_label(self, obj):
        return obj.get_action_display()