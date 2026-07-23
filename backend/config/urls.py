"""
URL configuration for Didebaan Fraud & Abuse Intelligence Engine.
Issue #4: API documentation via drf-spectacular (Swagger UI + ReDoc).
"""
from django.urls import path, include
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.views import obtain_auth_token
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from aml.views import dashboard_view
from aml.admin import aml_admin_site

urlpatterns = [
    path('', dashboard_view),
    path('admin/', aml_admin_site.urls),

    # Issue #4: OpenAPI schema + Swagger UI + ReDoc
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Token auth
    path('api/auth/token/', obtain_auth_token),

    # AML API endpoints
    path('api/', include('aml.urls')),
]
