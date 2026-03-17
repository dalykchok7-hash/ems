from django.urls import path
from produits.views import (
    ProduitListView,
    ProduitDetailView,
    VenteListView,
)

urlpatterns = [
    # Produits
    path('',
         ProduitListView.as_view(),
         name='produit-list'),

    path('<uuid:produit_id>/',
         ProduitDetailView.as_view(),
         name='produit-detail'),

    # Ventes
    path('ventes/',
         VenteListView.as_view(),
         name='vente-list'),
]