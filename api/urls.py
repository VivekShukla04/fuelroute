from django.urls import path
from api import views

urlpatterns = [
    path("route/", views.plan_route, name="plan-route"),
    path("health/", views.health_check, name="health-check"),
]
