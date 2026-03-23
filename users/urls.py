from django.urls import path
from users.views import (
    LoginView,
    LogoutView,
    CreerPersonnelView,
    DashboardStatsView,
    PersonnelListView,
    PersonnelDetailView,
)

urlpatterns = [
    path('login/',     LoginView.as_view(),          name='login'),
    path('logout/',    LogoutView.as_view(),          name='logout'),
    path('',           CreerPersonnelView.as_view(),  name='creer-personnel'),
    path('dashboard/', DashboardStatsView.as_view(),  name='dashboard-stats'),
    path('personnel/', PersonnelListView.as_view(),   name='personnel-list'),
    path('personnel/<uuid:personnel_id>/',
         PersonnelDetailView.as_view(),
         name='personnel-detail'),
]