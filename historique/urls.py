from django.urls import path
from historique.views import HistoriqueListView

urlpatterns = [
    path('',
         HistoriqueListView.as_view(),
         name='historique-list'),
]