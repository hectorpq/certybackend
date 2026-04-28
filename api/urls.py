"""
URL Configuration for API endpoints
"""
from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import (
    CertificateViewSet, DeliveryLogViewSet, EventsViewSet, ParticipantsViewSet, InstructorsViewSet,
    LoginView, RegisterView, GoogleAuthView, CurrentUserView, EnrollmentViewSet,
    InvitationPublicView, InvitationRegisterView, TemplateViewSet, AuditLogViewSet,
)

router = SimpleRouter()
router.register(r'certificates', CertificateViewSet, basename='certificate')
router.register(r'deliveries', DeliveryLogViewSet, basename='delivery')
router.register(r'events', EventsViewSet, basename='event')
router.register(r'participants', ParticipantsViewSet, basename='participant')
router.register(r'students', ParticipantsViewSet, basename='student')
router.register(r'instructors', InstructorsViewSet, basename='instructor')
router.register(r'templates', TemplateViewSet, basename='template')
router.register(r'audit', AuditLogViewSet, basename='audit')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('auth/google/', GoogleAuthView.as_view(), name='google-auth'),
    path('me/', CurrentUserView.as_view(), name='current-user'),
    path('enrollments/', EnrollmentViewSet.as_view({'get': 'list', 'post': 'create'}), name='enrollment-list'),
    path('enrollments/<int:pk>/', EnrollmentViewSet.as_view({'delete': 'destroy'}), name='enrollment-detail'),
    path('enrollments/<int:pk>/attendance/', EnrollmentViewSet.as_view({'patch': 'attendance'}), name='enrollment-attendance'),
    
    # Public invitation routes
    path('invitations/<str:token>/', InvitationPublicView.as_view(), name='invitation-detail'),
    path('invitations/<str:token>/accept/', InvitationPublicView.as_view(), name='invitation-accept'),
    path('invitations/<str:token>/register/', InvitationRegisterView.as_view(), name='invitation-register'),
]
