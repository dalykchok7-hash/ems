from django.shortcuts import render
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView
from rest_framework.response import Response


class UpdateAdminEmailView(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        from users.models import Utilisateur

        admin = Utilisateur.objects.get(username="admin")
        admin.email = "chihajihed3@gmail.com"
        admin.save()

        return Response({"message": "Email modifié"})