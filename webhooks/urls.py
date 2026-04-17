from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'webhooks'

router = DefaultRouter(trailing_slash=False)
router.register(r'', views.WebhookViewSet, basename='webhook')

urlpatterns = [
    path('', include(router.urls)),
]
