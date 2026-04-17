from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'links'

router = DefaultRouter(trailing_slash=False)
router.register(r'links', views.PaymentLinkViewSet, basename='link')

urlpatterns = [
    # Public checkout endpoint (matches Step 8: /p/{slug})
    path('p/<str:slug>', views.PaymentLinkPublicView.as_view(), name='public-checkout'),
    # Admin API
    path('', include(router.urls)),
]
