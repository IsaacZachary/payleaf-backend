from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'settlements'

router = DefaultRouter(trailing_slash=False)
router.register(r'', views.SettlementViewSet, basename='settlement')

urlpatterns = [
    path('', include(router.urls)),
]
