from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'payments'

router = DefaultRouter(trailing_slash=False)
router.register(r'', views.PaymentIntentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
]
