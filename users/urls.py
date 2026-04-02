from django.urls import path
from users.views import (
    LoginView,
    LogoutView,
    CreerPersonnelView,
    DashboardRevenusView,
    PersonnelListView,
    PersonnelDetailView,
    DashboardAlertesView,
    DashboardClientsView,
    ChangePasswordView,
)

urlpatterns = [
    path('login/',     LoginView.as_view(),          name='login'),
    path('logout/',    LogoutView.as_view(),          name='logout'),
    path('',           CreerPersonnelView.as_view(),  name='creer-personnel'),
    path('dashboard/revenus/', DashboardRevenusView.as_view(), name='dashboard-revenus'),
    path('dashboard/alertes/', DashboardAlertesView.as_view(), name='dashboard-alertes'),
    path('dashboard/clients/', DashboardClientsView.as_view(), name='dashboard-clients'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('personnel/', PersonnelListView.as_view(),   name='personnel-list'),
    path('personnel/<uuid:personnel_id>/',
         PersonnelDetailView.as_view(),
         name='personnel-detail'),
]