from django.urls import path
from clients.views import (
    ClientListView,
    ClientDetailView,
    ClientSeancesView,
    ClientStatsView,
    AbonnementClientView,
    AbonnementHistoriqueView,
    AbonnementDetailView,
    AbonnementListView,
    PackListView,
    PackDetailView,
)

urlpatterns = [
     path('packs/',                PackListView.as_view()),
    path('packs/<uuid:pack_id>/', PackDetailView.as_view()),
    # ✅ IMPORTANT — mettre AVANT <str:cin>
    path('abonnements/',
         AbonnementListView.as_view(),
         name='abonnement-list'),

    path('abonnements/<uuid:abonnement_id>/',
         AbonnementDetailView.as_view(),
         name='abonnement-detail'),

    # autres routes
    path('stats/',
         ClientStatsView.as_view(),
         name='client-stats'),

    path('<str:cin>/abonnement/',
         AbonnementClientView.as_view(),
         name='abonnement-actif'),

    path('<str:cin>/abonnements/',
         AbonnementHistoriqueView.as_view(),
         name='abonnement-historique'),

    path('<str:cin>/seances/',
         ClientSeancesView.as_view(),
         name='client-seances'),

    path('<str:cin>/',
         ClientDetailView.as_view(),
         name='client-detail'),

    path('',
         ClientListView.as_view(),
         name='client-list'),
]