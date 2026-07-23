"""
URL configuration for AML app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'customers', views.CustomerViewSet, basename='customer')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'alerts', views.AlertViewSet, basename='alert')
router.register(r'risk-scores', views.RiskScoreViewSet, basename='riskscore')
router.register(r'rules', views.RuleViewSet, basename='rule')
router.register(r'reports', views.ReportViewSet, basename='report')
router.register(r'audit-log', views.AuditLogViewSet, basename='auditlog')
router.register(r'devices', views.DeviceViewSet, basename='device')
router.register(r'merchants', views.MerchantViewSet, basename='merchant')

urlpatterns = [
    path('health/', views.HealthView.as_view()),
    path('ready/', views.ReadyView.as_view()),
    path('', include(router.urls)),
]

