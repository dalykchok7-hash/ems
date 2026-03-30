from rest_framework.views    import APIView
from rest_framework.response import Response
from rest_framework          import status
from rest_framework.pagination import PageNumberPagination

from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

from users.permissions  import IsAdmin
from users.models       import Utilisateur
from users.serializers  import UtilisateurSerializer, CreerPersonnelSerializer, ModifierPersonnelSerializer
from users.services     import AuthService


class CreerPersonnelView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(
        summary   = 'Créer un membre du personnel',
        request   = CreerPersonnelSerializer,
        responses = {
            201: UtilisateurSerializer,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
        }
    )
    def post(self, request):
        serializer = CreerPersonnelSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            personnel = AuthService.creer_personnel(
                serializer.validated_data
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            UtilisateurSerializer(personnel).data,
            status=status.HTTP_201_CREATED
        )


class PersonnelListView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(
        summary   = 'Liste du personnel',
        responses = {200: UtilisateurSerializer(many=True)}
    )
    def get(self, request):
        personnel  = Utilisateur.objects.filter(
            role='personnel'
        ).order_by('username')

        paginator  = PageNumberPagination()
        page       = paginator.paginate_queryset(personnel, request)
        serializer = UtilisateurSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class PersonnelDetailView(APIView):
    permission_classes = [IsAdmin]

    def get_object(self, personnel_id):
        try:
            return Utilisateur.objects.get(
                id   = personnel_id,
                role = 'personnel'
            )
        except Utilisateur.DoesNotExist:
            return None

    @extend_schema(
        summary   = 'Détail d\'un membre du personnel',
        responses = {
            200: UtilisateurSerializer,
            404: OpenApiTypes.OBJECT,
        }
    )
    def get(self, request, personnel_id):
        personnel = self.get_object(personnel_id)
        if not personnel:
            return Response(
                {'error': 'Personnel non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(UtilisateurSerializer(personnel).data)

    @extend_schema(
        summary   = 'Modifier un membre du personnel',
        request   = ModifierPersonnelSerializer,
        responses = {
            200: UtilisateurSerializer,
            404: OpenApiTypes.OBJECT,
        }
    )
    def put(self, request, personnel_id):
        personnel = self.get_object(personnel_id)
        if not personnel:
            return Response(
                {'error': 'Personnel non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = ModifierPersonnelSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        champs_modifiables = [
            'first_name', 'last_name', 'email',
            'cin', 'telephone', 'role', 'shift', 'date_embauche'
        ]

        for champ, valeur in serializer.validated_data.items():
            setattr(personnel, champ, valeur)
        personnel.save()
        
        return Response(UtilisateurSerializer(personnel).data)

    @extend_schema(
        summary   = 'Activer / Désactiver un membre du personnel',
        request   = None,
        responses = {
            200: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        }
    )
    def patch(self, request, personnel_id):
        personnel = self.get_object(personnel_id)
        if not personnel:
            return Response(
                {'error': 'Personnel non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

        personnel.is_active = not personnel.is_active
        personnel.save()

        statut = 'activé' if personnel.is_active else 'désactivé'
        return Response({
            'message'  : f"Compte {statut} avec succès",
            'is_active': personnel.is_active
        })

    @extend_schema(
        summary   = 'Supprimer un membre du personnel',
        request   = None,
        responses = {
            200: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        }
    )
    def delete(self, request, personnel_id):
        personnel = self.get_object(personnel_id)
        if not personnel:
            return Response(
                {'error': 'Personnel non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

        personnel.delete()
        return Response(
            {'message': 'Personnel supprimé avec succès'},
            status=status.HTTP_200_OK
        )