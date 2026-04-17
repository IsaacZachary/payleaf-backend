from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'refunds'

router = DefaultRouter(trailing_slash=False)
router.register(r'', views.RefundViewSet, basename='refund')

urlpatterns = [
    path('', include(router.urls)),
]
