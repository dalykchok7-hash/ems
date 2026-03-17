from rest_framework.views    import APIView
from rest_framework.response import Response
from rest_framework          import status
from datetime                import date

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from users.permissions              import IsAdminOrPersonnel
from historique.serializers         import HistoriqueSerializer
from historique.services            import HistoriqueService


class HistoriqueListView(APIView):
    permission_classes = [IsAdminOrPersonnel]

    @extend_schema(
        summary     = 'Historique des actions',
        description = 'Retourne l\'historique des actions. Par défaut aujourd\'hui.',
        parameters  = [
            OpenApiParameter(
                name        = 'date',
                type        = str,
                location    = OpenApiParameter.QUERY,
                description = 'Date au format YYYY-MM-DD',
                required    = False,
            )
        ],
        responses   = {200: HistoriqueSerializer(many=True)}
    )
    def get(self, request):
        date_param = request.query_params.get('date', None)

        if date_param:
            try:
                date_filtre = date.fromisoformat(date_param)
            except ValueError:
                return Response(
                    {'error': 'Format date invalide. Utilisez YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            date_filtre = date.today()

        historiques = HistoriqueService.liste(date_filtre)
        serializer  = HistoriqueSerializer(historiques, many=True)
        return Response(serializer.data)