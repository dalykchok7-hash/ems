from django.urls import path
from seances.views import (
    SeanceListView,
    SeanceReservationsView,
    ReservationDetailView,
    ReservationPresentView,
    ReservationAbsentView,
    ReservationAnnulerView,
)

urlpatterns = [
    # Créneaux
    path('',
         SeanceListView.as_view(),
         name='seance-list'),

    path('<uuid:seance_id>/reservations/',
         SeanceReservationsView.as_view(),
         name='seance-reservations'),

    # Réservations
    path('reservations/<uuid:reservation_id>/',
         ReservationDetailView.as_view(),
         name='reservation-detail'),

    path('reservations/<uuid:reservation_id>/present/',
         ReservationPresentView.as_view(),
         name='reservation-present'),

    path('reservations/<uuid:reservation_id>/absent/',
         ReservationAbsentView.as_view(),
         name='reservation-absent'),

    path('reservations/<uuid:reservation_id>/annuler/',
         ReservationAnnulerView.as_view(),
         name='reservation-annuler'),
]