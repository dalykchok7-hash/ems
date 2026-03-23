from rest_framework.views    import APIView
from rest_framework.response import Response
from rest_framework          import status

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from users.permissions  import IsAdmin
from users.models       import Utilisateur
from users.serializers  import UtilisateurSerializer


class PersonnelListView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(
        summary   = 'Liste du personnel',
        responses = {200: UtilisateurSerializer(many=True)}
    )
    def get(self, request):
        personnel = Utilisateur.objects.filter(
            role = 'personnel'
        ).order_by('username')

        from rest_framework.pagination import PageNumberPagination
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
        summary   = 'Modifier un membre du personnel',
        request   = None,
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

        champs_modifiables = [
            'first_name', 'last_name', 'telephone',
            'shift', 'date_embauche'
        ]

        for champ in champs_modifiables:
            if champ in request.data:
                setattr(personnel, champ, request.data[champ])

        personnel.save()
        return Response(UtilisateurSerializer(personnel).data)

    @extend_schema(
        summary   = 'Désactiver un membre du personnel',
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
            'message' : f"Compte {statut} avec succès",
            'is_active': personnel.is_active
        })