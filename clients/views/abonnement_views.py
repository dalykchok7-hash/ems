from rest_framework.views    import APIView
from rest_framework.response import Response
from rest_framework          import status
from rest_framework.pagination import PageNumberPagination

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from users.permissions       import IsAdminOrPersonnel, IsAdmin
from clients.models          import Client, Abonnement, Pack
from clients.serializers     import (
    AbonnementSerializer, PackSerializer,
    CreerAbonnementSerializer, ModifierAbonnementSerializer,
    CreerPackSerializer, ModifierPackSerializer
)
from clients.services        import AbonnementService, PackService
from historique.services     import HistoriqueService


# ══════════════════════════════════════════════════════
#  PACKS
# ══════════════════════════════════════════════════════

class PackListView(APIView):
    permission_classes = [IsAdminOrPersonnel]

    @extend_schema(
        summary   = 'Liste des packs',
        responses = {200: PackSerializer(many=True)}
    )
    def get(self, request):
        """Retourne tous les packs actifs"""
        packs = Pack.objects.filter(est_actif=True)
        return Response(PackSerializer(packs, many=True).data)

    @extend_schema(
        summary   = 'Créer un pack',
        request   = CreerPackSerializer,
        responses = {201: PackSerializer, 400: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        """Créer un nouveau pack"""
        serializer = CreerPackSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        pack = PackService.creer_pack(serializer.validated_data)
        return Response(PackSerializer(pack).data, status=status.HTTP_201_CREATED)


class PackDetailView(APIView):
    permission_classes = [IsAdminOrPersonnel]

    @extend_schema(
        summary   = 'Modifier un pack',
        request   = ModifierPackSerializer,
        responses = {200: PackSerializer, 404: OpenApiTypes.OBJECT}
    )
    def put(self, request, pack_id):
        """Modifier nom, nb_seances, prix ou description d'un pack"""
        serializer = ModifierPackSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        resultat = PackService.modifier_pack(pack_id, serializer.validated_data)
        if isinstance(resultat, dict) and 'error' in resultat:
            return Response(resultat, status=status.HTTP_404_NOT_FOUND)

        return Response(PackSerializer(resultat).data)

    @extend_schema(
        summary   = 'Désactiver un pack',
        responses = {200: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
    )
    def delete(self, request, pack_id):
        """Désactive le pack (soft delete — les abonnements existants sont conservés)"""
        resultat = PackService.desactiver_pack(pack_id)
        if isinstance(resultat, dict) and 'error' in resultat:
            return Response(resultat, status=status.HTTP_404_NOT_FOUND)
        return Response(resultat)


# ══════════════════════════════════════════════════════
#  ABONNEMENTS
# ══════════════════════════════════════════════════════

class AbonnementClientView(APIView):
    permission_classes = [IsAdminOrPersonnel]

    @extend_schema(
        summary   = 'Abonnement actif d\'un client',
        responses = {200: AbonnementSerializer, 404: OpenApiTypes.OBJECT}
    )
    def get(self, request, cin):
        try:
            client = Client.objects.get(cin=cin)
        except Client.DoesNotExist:
            return Response({'error': 'Client non trouvé'}, status=status.HTTP_404_NOT_FOUND)

        abonnement = client.abonnement_actif

        if not abonnement:
            return Response({
                "id"               : None,
                "pack"             : None,
                "pack_detail"      : None,
                "date_debut"       : None,
                "date_expiration"  : None,
                "seances_total"    : 0,
                "seances_utilisees": 0,
                "seances_restantes": 0,
                "statut"           : None,
                "mode_paiement"    : None,
                "est_paye"         : False,
                "prix_paye"        : None,
                "reduction"        : 0,
            }, status=status.HTTP_200_OK)

        data = AbonnementSerializer(abonnement).data
        data['seances_utilisees'] = abonnement.seances_total - abonnement.seances_restantes
        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(
        summary   = 'Créer un abonnement',
        request   = CreerAbonnementSerializer,
        responses = {201: AbonnementSerializer, 400: OpenApiTypes.OBJECT}
    )
    def post(self, request, cin):
        try:
            client = Client.objects.get(cin=cin)
        except Client.DoesNotExist:
            return Response({'error': 'Client non trouvé'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CreerAbonnementSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            abonnement = AbonnementService.creer_abonnement(client, serializer.validated_data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            HistoriqueService.creer_abonnement(request.user, abonnement)
        except Exception as e:
            print(f"ERROR: Failed to create history entry for abonnement: {e}")

        return Response(AbonnementSerializer(abonnement).data, status=status.HTTP_201_CREATED)


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
            return Response({'error': 'Client non trouvé'}, status=status.HTTP_404_NOT_FOUND)

        abonnements = AbonnementService.historique_abonnements(client)
        return Response(AbonnementSerializer(abonnements, many=True).data)


class AbonnementDetailView(APIView):
    permission_classes = [IsAdminOrPersonnel]

    @extend_schema(
        summary   = 'Modifier un abonnement',
        request   = ModifierAbonnementSerializer,
        responses = {200: AbonnementSerializer, 404: OpenApiTypes.OBJECT}
    )
    def put(self, request, abonnement_id):
        serializer = ModifierAbonnementSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        resultat = AbonnementService.modifier(abonnement_id, serializer.validated_data)
        if isinstance(resultat, dict) and 'error' in resultat:
            return Response(resultat, status=status.HTTP_404_NOT_FOUND)

        return Response(AbonnementSerializer(resultat).data)

    @extend_schema(
        summary   = 'Supprimer un abonnement',
        responses = {200: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
    )
    def delete(self, request, abonnement_id):
        resultat = AbonnementService.supprimer(abonnement_id)
        if isinstance(resultat, dict) and 'error' in resultat:
            return Response(resultat, status=status.HTTP_404_NOT_FOUND)
        return Response(resultat)


class AbonnementListView(APIView):
    permission_classes = [IsAdminOrPersonnel]

    @extend_schema(
        summary    = 'Liste de tous les abonnements',
        parameters = [
            OpenApiParameter(name='statut', type=str, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter(name='q',      type=str, location=OpenApiParameter.QUERY, required=False),
        ],
        responses  = {200: AbonnementSerializer(many=True)}
    )
    def get(self, request):
        from django.db.models import Q

        abonnements = Abonnement.objects.all().select_related('client', 'pack').order_by('-created_at')

        statut = request.query_params.get('statut')
        if statut:
            abonnements = abonnements.filter(statut=statut)

        q = request.query_params.get('q')
        if q:
            abonnements = abonnements.filter(
                Q(client__nom__icontains=q)    |
                Q(client__prenom__icontains=q) |
                Q(client__cin__icontains=q)
            )

        paginator  = PageNumberPagination()
        page       = paginator.paginate_queryset(abonnements, request)
        serializer = AbonnementSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)