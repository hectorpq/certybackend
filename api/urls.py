"""
URL Configuration for API endpoints
"""
from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import CertificateViewSet, DeliveryLogViewSet

# Create router and register viewsets
router = SimpleRouter()
router.register(r'certificates', CertificateViewSet, basename='certificate')
router.register(r'deliveries', DeliveryLogViewSet, basename='delivery')

# Include router URLs
urlpatterns = [
    path('', include(router.urls)),
]
