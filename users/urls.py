from django.urls import path
from users.views import LoginView, CreerPersonnelView,DashboardStatsView

urlpatterns = [
    path('login/',    LoginView.as_view()),
    path('',          CreerPersonnelView.as_view()),
    path('dashboard/', DashboardStatsView.as_view(),  name='dashboard-stats'),
]