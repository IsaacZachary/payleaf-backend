from django.urls import path
from . import views

app_name = 'auditlog'

urlpatterns = [
    path('', views.AuditLogList.as_view(), name='audit-log-list'),
    path('export', views.AuditLogExport.as_view(), name='audit-log-export'),
    path('<uuid:pk>', views.AuditLogDetail.as_view(), name='audit-log-detail'),
]
