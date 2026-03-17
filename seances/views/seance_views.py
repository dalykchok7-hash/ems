from historique.services.historique_service import HistoriqueService
from rest_framework.views    import APIView
from rest_framework.response import Response
from rest_framework          import status
from datetime                import date

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from users.permissions              import IsAdminOrPersonnel
from seances.models                 import Seance
from seances.serializers            import SeanceSerializer, ReservationSerializer, CreerReservationSerializer,CreerReservationSwaggerSerializer
from seances.services               import ReservationService
from historique.services import HistoriqueService

class SeanceListView(APIView):
    permission_classes = [IsAdminOrPersonnel]

    @extend_schema(
        summary     = 'Liste des créneaux',
        description = 'Retourne les créneaux d\'une date. Par défaut aujourd\'hui.',
        parameters  = [
            OpenApiParameter(
                name        = 'date',
                type        = str,
                location    = OpenApiParameter.QUERY,
                description = 'Date au format YYYY-MM-DD',
                required    = False,
            )
        ],
        responses   = {200: SeanceSerializer(many=True)}
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

        seances = Seance.objects.filter(
            date=date_filtre
        ).order_by('heure_debut')

        serializer = SeanceSerializer(seances, many=True)
        return Response(serializer.data)


class SeanceReservationsView(APIView):
    permission_classes = [IsAdminOrPersonnel]

    @extend_schema(
        summary   = 'Réservations d\'un créneau',
        responses = {
            200: ReservationSerializer(many=True),
            404: OpenApiTypes.OBJECT,
        }
    )
    def get(self, request, seance_id):
        try:
            seance = Seance.objects.get(id=seance_id)
        except Seance.DoesNotExist:
            return Response(
                {'error': 'Créneau non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        reservations = seance.reservations.filter(
            statut__in=['en_attente', 'present']
        ).select_related('abonnement__client')

        serializer = ReservationSerializer(reservations, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary   = 'Créer une réservation',
        request   = CreerReservationSwaggerSerializer,
        responses = {
            201: ReservationSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        }
    )
    def post(self, request, seance_id):
        if not Seance.objects.filter(id=seance_id).exists():
            return Response(
                {'error': 'Créneau non trouvé'},
                status=status.HTTP_404_NOT_FOUND
        )

        data = request.data.copy()
        data['seance_id'] = str(seance_id)

        serializer = CreerReservationSerializer(data=data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            reservation = ReservationService.creer_reservation(
                abonnement    = serializer.validated_data['abonnement'],
                seance        = serializer.validated_data['seance'],
                type_appareil = serializer.validated_data['type_appareil'],
                personnel     = request.user,
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
        )
        try:
            HistoriqueService.creer_reservation(request.user, reservation)
        except Exception:
            pass

        return Response(
            ReservationSerializer(reservation).data,
            status=status.HTTP_201_CREATED
        )