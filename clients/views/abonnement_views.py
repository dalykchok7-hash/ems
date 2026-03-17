from historique.services.historique_service import HistoriqueService
from rest_framework.views    import APIView
from rest_framework.response import Response
from rest_framework          import status

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from users.permissions               import IsAdminOrPersonnel
from clients.serializers             import AbonnementSerializer, CreerAbonnementSerializer, ModifierAbonnementSerializer
from clients.services                import AbonnementService
from clients.models                  import Client
from historique.services import HistoriqueService


class AbonnementClientView(APIView):
    permission_classes = [IsAdminOrPersonnel]

    @extend_schema(
        summary     = 'Abonnement actif d\'un client',
        description = 'Retourne l\'abonnement actif ou en attente du client',
        responses   = {
            200: AbonnementSerializer,
            404: OpenApiTypes.OBJECT,
        }
    )
    def get(self, request, cin):
        try:
            client = Client.objects.get(cin=cin)
        except Client.DoesNotExist:
            return Response(
                {'error': 'Client non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

        abonnement = client.abonnement_actif
        if not abonnement:
            return Response(
                {'error': 'Aucun abonnement actif'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AbonnementSerializer(abonnement)
        data = serializer.data
        data['peut_reserver'] = abonnement.seances_restantes > 0
        return Response(data)

    @extend_schema(
        summary   = 'Créer un abonnement',
        request   = CreerAbonnementSerializer,
        responses = {
            201: AbonnementSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        }
    )
    def post(self, request, cin):
        try:
            client = Client.objects.get(cin=cin)
        except Client.DoesNotExist:
         return Response(
            {'error': 'Client non trouvé'},
            status=status.HTTP_404_NOT_FOUND
        )

        serializer = CreerAbonnementSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            abonnement = AbonnementService.creer_abonnement(
            client, serializer.validated_data
        )
        except ValueError as e:
            return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
        try:
            HistoriqueService.creer_abonnement(request.user, abonnement)
        except Exception:
            pass
        return Response(
            AbonnementSerializer(abonnement).data,
        status=status.HTTP_201_CREATED
    )
    


class AbonnementHistoriqueView(APIView):
    permission_classes = [IsAdminOrPersonnel]

    @extend_schema(
        summary   = 'Historique des abonnements d\'un client',
        responses = {200: AbonnementSerializer(many=True)}
    )
    def get(self, request, cin):
        try:
            client = Client.objects.get(cin=cin)
        except Client.DoesNotExist:
            return Response(
                {'error': 'Client non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

        abonnements = AbonnementService.historique_abonnements(client)
        serializer  = AbonnementSerializer(abonnements, many=True)
        return Response(serializer.data)


class AbonnementDetailView(APIView):
    permission_classes = [IsAdminOrPersonnel]

    @extend_schema(
        summary   = 'Modifier un abonnement',
        request   = ModifierAbonnementSerializer,
        responses = {
            200: AbonnementSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        }
    )
    def put(self, request, abonnement_id):
        serializer = ModifierAbonnementSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        resultat = AbonnementService.modifier(
            abonnement_id, serializer.validated_data
        )

        if 'error' in resultat:
            return Response(
                resultat,
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(resultat)