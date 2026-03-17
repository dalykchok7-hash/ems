from django.urls import path
from clients.views import (
    ClientListView,
    ClientDetailView,
    AbonnementClientView,
    ClientSeancesView,
    ClientStatsView,
    AbonnementHistoriqueView,
    AbonnementDetailView,
)

urlpatterns = [
    path('',
         ClientListView.as_view(),
         name='client-list'),
     path('stats/',
         ClientStatsView.as_view(),
         name='client-stats'),
    path('<str:cin>/',
         ClientDetailView.as_view(),
         name='client-detail'),

     path('<str:cin>/seances/',
         ClientSeancesView.as_view(),
         name='client-seances'),

    path('<str:cin>/abonnement/',
         AbonnementClientView.as_view(),
         name='abonnement-actif'),

    path('<str:cin>/abonnements/',
         AbonnementHistoriqueView.as_view(),
         name='abonnement-historique'),

    path('abonnements/<uuid:abonnement_id>/',
         AbonnementDetailView.as_view(),
         name='abonnement-detail'),
]