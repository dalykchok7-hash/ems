from historique.services.historique_service import HistoriqueService
from rest_framework.views    import APIView
from rest_framework.response import Response
from rest_framework          import status
from rest_framework.pagination import PageNumberPagination
from clients.models import Abonnement
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework.pagination import PageNumberPagination
from users.permissions               import IsAdminOrPersonnel
from clients.serializers             import AbonnementSerializer, CreerAbonnementSerializer, ModifierAbonnementSerializer
from clients.services                import AbonnementService
from clients.models                  import Client, Abonnement
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
        {
            "id": None,   # ← ajoute ça aussi
            "nom_pack": None,
                    "date_debut": None,
                    "date_fin": None,
                    "seances_total": 0,
                    "seances_utilisees": 0,
                    "seances_restantes": 0,
                    "statut": None
        },
         status=status.HTTP_200_OK
        )

        seances_total = abonnement.seances_total
        seances_restantes = abonnement.seances_restantes
        seances_utilisees = seances_total - seances_restantes

        # 🔥 RÉPONSE FORMAT FRONT
        data = {
            "id": abonnement.id,   # ← ajoute ça
            "nom_pack": abonnement.get_type_display(),
            "date_debut": abonnement.date_debut,
            "date_fin": abonnement.date_expiration,
            "seances_total": seances_total,
            "seances_utilisees": seances_utilisees,
            "seances_restantes": seances_restantes,
            "statut": abonnement.statut,
            # ✅ AJOUTS CRITIQUES
            "mode_paiement": abonnement.mode_paiement,
            "est_paye": abonnement.est_paye,
            "prix_paye": str(abonnement.prix_paye),  # 👈 important
            "reduction": str(abonnement.reduction),  # 👈 important
        }

        return Response(data, status=status.HTTP_200_OK)

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

        if isinstance(resultat, dict) and 'error' in resultat:
            return Response(
                resultat,
                status=status.HTTP_404_NOT_FOUND
        )

        return Response(
            AbonnementSerializer(resultat).data,
            status=status.HTTP_200_OK
        )
class AbonnementListView(APIView):
    permission_classes = [IsAdminOrPersonnel]

    @extend_schema(
        summary    = 'Liste de tous les abonnements',
        parameters = [
            OpenApiParameter(
                name        = 'statut',
                type        = str,
                location    = OpenApiParameter.QUERY,
                description = 'Filtrer par statut : actif, en_attente, termine, expire',
                required    = False,
            ),
            OpenApiParameter(
                name        = 'q',
                type        = str,
                location    = OpenApiParameter.QUERY,
                description = 'Rechercher par nom ou CIN du client',
                required    = False,
            ),
        ],
        responses  = {200: AbonnementSerializer(many=True)}
    )
    def get(self, request):
        from django.db.models import Q

        abonnements = Abonnement.objects.all().select_related('client').order_by('-created_at')

        # Filtre par statut
        statut = request.query_params.get('statut', None)
        if statut:
            abonnements = abonnements.filter(statut=statut)

        # Recherche par nom ou CIN client
        q = request.query_params.get('q', None)
        if q:
            abonnements = abonnements.filter(
                Q(client__nom__icontains=q)    |
                Q(client__prenom__icontains=q) |
                Q(client__cin__icontains=q)
            )

        # Pagination
        paginator  = PageNumberPagination()
        page       = paginator.paginate_queryset(abonnements, request)
        serializer = AbonnementSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)