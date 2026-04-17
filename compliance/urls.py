from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'compliance'

router = DefaultRouter(trailing_slash=False)
router.register(r'', views.ComplianceViewSet, basename='compliance')

urlpatterns = [
    path('', include(router.urls)),
]
