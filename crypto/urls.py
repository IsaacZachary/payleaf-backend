from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'crypto'

router = DefaultRouter(trailing_slash=False)
router.register(r'', views.CryptoViewSet, basename='crypto')

urlpatterns = [
    path('', include(router.urls)),
]
