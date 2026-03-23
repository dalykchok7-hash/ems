from django.urls import path
from users.views import (
    LoginView,
    CreerPersonnelView,
    LogoutView,
    DashboardStatsView,
    PersonnelListView,
    PersonnelDetailView,
)

urlpatterns = [
    path('login/',    LoginView.as_view()),
    path('logout/',             LogoutView.as_view(),         name='logout'),
    path('',          CreerPersonnelView.as_view()),
    path('dashboard/', DashboardStatsView.as_view(),  name='dashboard-stats'),
]