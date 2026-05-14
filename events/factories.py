"""
Factories para generar datos de prueba.

Utilizando factory-boy para crear objetos Django de forma declarativa.
Útil para simplificar la creación de datos en pruebas.

Referencia: https://factoryboy.readthedocs.io/
"""

import factory
from django.utils import timezone

from events.models import Event, EventCategory
from users.models import User


class UserFactory(factory.django.DjangoModelFactory):
    """
    Factory para crear usuarios de prueba.
    
    Ejemplo de uso:
        user = UserFactory(full_name="John Doe")
        users = UserFactory.create_batch(5)
    """
    
    class Meta:
        model = User
    
    full_name = factory.Faker('name')
    email = factory.Faker('email')
    is_active = True
    role = 'participante'


class EventCategoryFactory(factory.django.DjangoModelFactory):
    """
    Factory para crear categorías de eventos.
    
    Ejemplo de uso:
        category = EventCategoryFactory(name="Technology")
        categories = EventCategoryFactory.create_batch(3)
    """
    
    class Meta:
        model = EventCategory
    
    name = factory.Faker('word')
    description = factory.Faker('sentence')


class EventFactory(factory.django.DjangoModelFactory):
    """
    Factory para crear eventos de prueba.
    
    Ejemplo de uso:
        event = EventFactory(name="Python Workshop")
        events = EventFactory.create_batch(10)
        event_with_user = EventFactory(created_by=my_user)
    """
    
    class Meta:
        model = Event
    
    # Campos simples
    name = factory.Faker('sentence', nb_words=3)
    description = factory.Faker('text')
    location = factory.Faker('city')
    status = 'active'
    duration_hours = factory.Faker('random_int', min=1, max=8)
    max_capacity = factory.Faker('random_int', min=10, max=100)
    
    # Campos de fecha
    event_date = factory.Faker('future_date')
    end_date = factory.Faker('future_date')
    
    # Relaciones
    created_by = factory.SubFactory(UserFactory)
    category = factory.SubFactory(EventCategoryFactory)
    
    # Booleanos
    is_active = True
    auto_send_certificates = False
    is_public = True
    
    class Params:
        # Permite usar: EventFactory(archived=True) para cambiar múltiples campos
        archived = factory.Trait(
            status='finished',
            is_active=False,
        )
        private = factory.Trait(
            is_public=False,
        )


# ============================================================================
# EJEMPLO DE USO EN TESTS
# ============================================================================

"""
from events.factories import EventFactory, UserFactory

# Crear un evento simple
event = EventFactory()

# Crear evento con valores específicos
event = EventFactory(name="Django Masterclass", status="draft")

# Crear múltiples eventos
events = EventFactory.create_batch(10)

# Usar traits
archived_event = EventFactory(archived=True)

# Crear con relaciones customizadas
user = UserFactory(email="instructor@example.com")
event = EventFactory(created_by=user)

# Usar en fixtures
@pytest.fixture
def create_test_event():
    return EventFactory()

@pytest.fixture
def create_test_events_batch():
    return EventFactory.create_batch(5)
"""
