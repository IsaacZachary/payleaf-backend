from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'apikeys'

router = DefaultRouter()
router.register(r'', views.ApiKeyViewSet, basename='api-key')

urlpatterns = [
    path('', include(router.urls)),
]
