import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from rest_framework.test import APIRequestFactory
from api.views import StudentsViewSet
from students.models import Student

# Crear request factory
factory = APIRequestFactory()

# Crear una request POST simulada
request = factory.post('/api/students/', {
    'document_id': 'TEST123',
    'first_name': 'Test',
    'last_name': 'User',
    'email': 'test_create@example.com',
    'phone': '1234567890'
}, format='json')

# Simular usuario autenticado (necesario para el permission)
from users.models import User
try:
    user = User.objects.get(email='admin@admin.com')
except User.DoesNotExist:
    user = User.objects.first()

request.user = user

# Ejecutar la vista
view = StudentsViewSet.as_view({'post': 'create'})
try:
    response = view(request)
    print(f"Status: {response.status_code}")
    print(f"Data: {response.data}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
