from rest_framework.views    import APIView
from rest_framework.response import Response
from rest_framework          import status
from datetime                import date

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from users.permissions    import IsAdminOrPersonnel
from produits.serializers import VenteSerializer, CreerVenteSerializer
from produits.services    import VenteService
from historique.services import HistoriqueService

class VenteListView(APIView):
    permission_classes = [IsAdminOrPersonnel]

    @extend_schema(
        summary    = 'Historique des ventes',
        parameters = [
            OpenApiParameter(
                name        = 'date',
                type        = str,
                location    = OpenApiParameter.QUERY,
                description = 'Filtrer par date YYYY-MM-DD',
                required    = False,
            )
        ],
        responses  = {200: VenteSerializer(many=True)}
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
            date_filtre = None

        ventes     = VenteService.historique(date_filtre)
        serializer = VenteSerializer(ventes, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary   = 'Créer une vente',
        request   = CreerVenteSerializer,
        responses = {
            201: VenteSerializer,
            400: OpenApiTypes.OBJECT,
        }
    )
    def post(self, request):
        serializer = CreerVenteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        vente = VenteService.creer_vente(
            lignes    = serializer.validated_data['lignes'],
            personnel = request.user,
        )
        try:
            HistoriqueService.creer_vente(request.user, vente)
        except Exception:
            pass

        return Response(
            VenteSerializer(vente).data,
            status=status.HTTP_201_CREATED
        )