"""
URL Configuration for API endpoints
"""
from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import CertificateViewSet, DeliveryLogViewSet, EventsViewSet, StudentsViewSet

# Create router and register viewsets
router = SimpleRouter()
router.register(r'certificates', CertificateViewSet, basename='certificate')
router.register(r'deliveries', DeliveryLogViewSet, basename='delivery')
router.register(r'events', EventsViewSet, basename='event')
router.register(r'students', StudentsViewSet, basename='student')

# Include router URLs
urlpatterns = [
    path('', include(router.urls)),
]
