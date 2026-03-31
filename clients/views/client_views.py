from rest_framework.views    import APIView
from rest_framework.response import Response
from rest_framework          import status

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from users.permissions   import IsAdminOrPersonnel
from clients.models      import Client
from clients.serializers import ClientSerializer, CreerClientSerializer, ModifierClientSerializer
from clients.services    import ClientService
from historique.services import HistoriqueService
from rest_framework.pagination import PageNumberPagination
from seances.models import Reservation
from django.db.models import Count
from datetime import date
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Q

class ClientListView(APIView):
    permission_classes = [IsAdminOrPersonnel]
    parser_classes     = [MultiPartParser, FormParser, JSONParser]

    @extend_schema(
        summary     = 'Liste des clients',
        description = 'Retourne tous les clients. Recherche possible par nom, prénom, CIN, téléphone.',
        parameters  = [
            OpenApiParameter(
                name        = 'q',
                type        = str,
                location    = OpenApiParameter.QUERY,
                description = 'Rechercher par nom, prénom, CIN, téléphone',
                required    = False,
            )
        ],
        responses   = {200: ClientSerializer(many=True)}
    )
    def get(self, request):
        q = request.query_params.get('q', None)
        if q:
            clients = Client.objects.filter(
                Q(nom__icontains=q) |
                Q(prenom__icontains=q) |
                Q(cin__icontains=q) |
                Q(telephone_1__icontains=q) |
                Q(telephone_2__icontains=q)
            )
        else:
            clients = Client.objects.all()

        paginator   = PageNumberPagination()
        page        = paginator.paginate_queryset(clients, request)
        serializer = ClientSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        summary   = 'Créer un client',
        request   = CreerClientSerializer,
        responses = {
            201: ClientSerializer,
            400: OpenApiTypes.OBJECT,
        }
    )
    def post(self, request):
        serializer = CreerClientSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            client = ClientService.creer_client(serializer.validated_data)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            HistoriqueService.creer_client(request.user, client)
        except Exception:
            pass

        return Response(
            ClientSerializer(client).data,
            status=status.HTTP_201_CREATED
        )


class ClientDetailView(APIView):
    permission_classes = [IsAdminOrPersonnel]

    @extend_schema(
        summary   = 'Détail d\'un client',
        responses = {
            200: ClientSerializer,
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
        serializer = ClientSerializer(client)
        return Response(serializer.data)

    @extend_schema(
        summary   = 'Modifier un client',
        request   = ModifierClientSerializer,
        responses = {
            200: ClientSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        }
    )
    def put(self, request, cin):
        try:
            client = Client.objects.get(cin=cin)
        except Client.DoesNotExist:
            return Response(
                {'error': 'Client non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ModifierClientSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            client = ClientService.modifier_client(
                client, serializer.validated_data
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(ClientSerializer(client).data)
    @extend_schema(
    summary='Supprimer un client',
    responses={
        204: None,
        404: OpenApiTypes.OBJECT,
    }
    )
    def delete(self, request, cin):
        try:
            client = Client.objects.get(cin=cin)
            ClientService.supprimer_client(client)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        except Client.DoesNotExist:
            return Response(
            {'error': 'Client non trouvé'},
            status=status.HTTP_404_NOT_FOUND
            )

class ClientSeancesView(APIView):
    permission_classes = [IsAdminOrPersonnel]

    @extend_schema(
        summary     = 'Historique séances d\'un client',
        description = 'Retourne toutes les réservations d\'un client',
        responses   = {
            200: OpenApiTypes.OBJECT,
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

        reservations = Reservation.objects.filter(
            abonnement__client = client
        ).select_related(
            'seance', 'abonnement'
        ).order_by('-seance__date', '-seance__heure_debut')

        data = [
            {
            'id'           : str(r.id),
            'date'         : str(r.seance.date),
            'heure_debut'  : str(r.seance.heure_debut),  # ← corrigé
            'heure_fin'    : str(r.seance.heure_fin),     # ← ajouté
            'type_appareil': r.type_appareil,
            'type_label'   : r.get_type_appareil_display(),
            'statut'       : r.statut,
            'statut_label' : r.get_statut_display(),
            'taille_gilet' : r.taille_gilet,              # ← ajouté
    }
            for r in reservations
        ]

        return Response({
            'client'      : f"{client.prenom} {client.nom}",
            'total'       : len(data),
            'reservations': data,
        })


class ClientStatsView(APIView):
    permission_classes = [IsAdminOrPersonnel]

    @extend_schema(
        summary   = 'Statistiques clients',
        responses = {200: OpenApiTypes.OBJECT}
    )
    def get(self, request):
        aujourd_hui = date.today()
        debut_mois  = aujourd_hui.replace(day=1)

        # Total clients
        total_clients = Client.objects.count()

        # Nouveaux ce mois
        nouveaux_mois = Client.objects.filter(
            created_at__date__gte = debut_mois
        ).count()

        # Abonnés actifs
        abonnes_actifs = Client.objects.filter(
            abonnements__statut__in = ['actif', 'en_attente']
        ).distinct().count()

        # Expirations proches
        from clients.models import Abonnement
        expirations = Abonnement.objects.filter(
            statut__in             = ['actif', 'en_attente'],
            seances_restantes__lte = 2,
            seances_restantes__gt  = 0,
        ).values('client').distinct().count()

        # Clients inactifs
        clients_inactifs = Client.objects.exclude(
            abonnements__statut__in = ['actif', 'en_attente']
        ).distinct().count()

        # Séances ce mois
        from seances.models import Reservation
        seances_mois = Reservation.objects.filter(
            created_at__date__gte = debut_mois,
            statut                = 'present'
        ).count()

        return Response({
            'total_clients'    : total_clients,
            'nouveaux_mois'    : nouveaux_mois,
            'abonnes_actifs'   : abonnes_actifs,
            'expirations_proches': expirations,
            'clients_inactifs' : clients_inactifs,
            'seances_ce_mois'  : seances_mois,
        })