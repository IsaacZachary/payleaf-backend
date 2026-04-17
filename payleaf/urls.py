"""
PayLeaf root URL configuration.
All API endpoints are namespaced under /v1/ as per the API contract.
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),

    # API v1
    path('v1/auth/', include('accounts.urls')),
    path('v1/audit-logs/', include('auditlog.urls')),
    path('v1/api-keys/', include('apikeys.urls')),
    path('v1/customers/', include('customers.urls')),
    path('v1/payments/', include('payments.urls')),
    path('v1/crypto/', include('crypto.urls')),
    path('v1/refunds/', include('refunds.urls')),
    path('v1/links/', include('links.urls')),
    path('v1/settlements/', include('settlements.urls')),
    path('v1/compliance/', include('compliance.urls')),
    path('v1/webhooks/', include('webhooks.urls')),
]
