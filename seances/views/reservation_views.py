from historique.services.historique_service import HistoriqueService
from rest_framework.views    import APIView
from rest_framework.response import Response
from rest_framework          import status

from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

from users.permissions    import IsAdminOrPersonnel
from seances.models       import Reservation
from seances.serializers  import ReservationSerializer
from seances.services     import ReservationService
from historique.services import HistoriqueService

class ReservationDetailView(APIView):
    permission_classes = [IsAdminOrPersonnel]

    @extend_schema(
        summary   = 'Détail d\'une réservation',
        responses = {
            200: ReservationSerializer,
            404: OpenApiTypes.OBJECT,
        }
    )
    def get(self, request, reservation_id):
        try:
            reservation = Reservation.objects.get(id=reservation_id)
        except Reservation.DoesNotExist:
            return Response(
                {'error': 'Réservation non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(ReservationSerializer(reservation).data)


class ReservationPresentView(APIView):
    permission_classes = [IsAdminOrPersonnel]

    @extend_schema(
        summary   = 'Marquer présent',
        request   = None,
        responses = {
            200: ReservationSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        }
    )
    def patch(self, request, reservation_id):
        try:
            reservation = Reservation.objects.get(id=reservation_id)
        except Reservation.DoesNotExist:
            return Response(
                {'error': 'Réservation non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            reservation = ReservationService.marquer_present(reservation)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            HistoriqueService.marquer_present(request.user, reservation)
        except Exception:
            pass

        return Response(ReservationSerializer(reservation).data)


class ReservationAbsentView(APIView):
    permission_classes = [IsAdminOrPersonnel]

    @extend_schema(
        summary   = 'Marquer absent',
        request   = None,
        responses = {
            200: ReservationSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        }
    )
    def patch(self, request, reservation_id):
        try:
            reservation = Reservation.objects.get(id=reservation_id)
        except Reservation.DoesNotExist:
            return Response(
                {'error': 'Réservation non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            reservation = ReservationService.marquer_absent(reservation)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(ReservationSerializer(reservation).data)


class ReservationAnnulerView(APIView):
    permission_classes = [IsAdminOrPersonnel]

    @extend_schema(
        summary   = 'Annuler une réservation',
        request   = None,
        responses = {
            200: ReservationSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        }
    )
    def patch(self, request, reservation_id):
        try:
            reservation = Reservation.objects.get(id=reservation_id)
        except Reservation.DoesNotExist:
            return Response(
                {'error': 'Réservation non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            reservation = ReservationService.annuler(reservation)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(ReservationSerializer(reservation).data)