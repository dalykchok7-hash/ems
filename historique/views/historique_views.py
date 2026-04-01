from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import date, timedelta

from drf_spectacular.utils import extend_schema, OpenApiParameter

from users.permissions import IsAdminOrPersonnel
from historique.serializers import HistoriqueSerializer
from historique.services import HistoriqueService


class HistoriqueListView(APIView):
    permission_classes = [IsAdminOrPersonnel]

    @extend_schema(
        summary="Historique des actions",
        description="Retourne l'historique (7 derniers jours par défaut) avec filtres possibles.",
        parameters=[
            OpenApiParameter(name='date', type=str, description='YYYY-MM-DD', required=False),
            OpenApiParameter(name='date_debut', type=str, description='YYYY-MM-DD', required=False),
            OpenApiParameter(name='date_fin', type=str, description='YYYY-MM-DD', required=False),
        ],
        responses={200: HistoriqueSerializer(many=True)}
    )
    def get(self, request):

        date_param = request.query_params.get('date')
        date_debut_param = request.query_params.get('date_debut')
        date_fin_param = request.query_params.get('date_fin')

        try:
            # ✅ 1. Filtre par date exacte
            if date_param:
                date_filtre = date.fromisoformat(date_param)
                historiques = HistoriqueService.liste_par_date(date_filtre)

            # ✅ 2. Filtre par intervalle
            elif date_debut_param and date_fin_param:
                date_debut = date.fromisoformat(date_debut_param)
                date_fin = date.fromisoformat(date_fin_param)
                historiques = HistoriqueService.liste_intervalle(date_debut, date_fin)

            # ✅ 3. Par défaut → 7 derniers jours
            else:
                date_fin = date.today()
                date_debut = date_fin - timedelta(days=7)
                historiques = HistoriqueService.liste_intervalle(date_debut, date_fin)

        except ValueError:
            return Response(
                {'error': 'Format date invalide. Utilisez YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = HistoriqueSerializer(historiques, many=True)
        return Response(serializer.data)