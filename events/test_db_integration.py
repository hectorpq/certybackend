"""
Pruebas de integración para la aplicación 'events'.

Utilizando Testcontainers con PostgreSQL real en lugar de una base de datos en memoria.
Equivalente al archivo ICategoriaRepositoryTest.java del ejemplo de Spring Boot.

Estructura de pruebas:
- Creación de eventos (save)
- Búsqueda por ID (findById)
- Listado de eventos (findAll)
- Actualización de eventos (update)
- Eliminación de eventos (delete)

Cada prueba se ejecuta en una transacción aislada que se revierte automáticamente.
"""

import logging
from datetime import datetime, timedelta
from typing import Callable

import pytest
from django.utils import timezone

from events.models import Event, EventCategory
from users.models import User

logger = logging.getLogger(__name__)

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
@pytest.mark.django_db
def create_test_user():
    """
    Fixture que crea un usuario de prueba.
    Equivalente a una clase de configuración en el setUp del test de Spring Boot.
    """
    user, created = User.objects.get_or_create(
        email="testuser@example.com",
        defaults={
            'full_name': 'Test User',
            'is_active': True,
            'role': 'participante',
        }
    )
    return user


@pytest.fixture
@pytest.mark.django_db
def create_test_category():
    """
    Fixture que crea una categoría de evento de prueba.
    """
    category, created = EventCategory.objects.get_or_create(
        name="Technology",
        defaults={'description': 'Technology events for testing'}
    )
    return category


@pytest.fixture
@pytest.mark.django_db
def create_test_event(create_test_user, create_test_category):
    """
    Fixture que crea un evento de prueba.
    Se ejecuta antes de cada test individual (scope='function').
    Equivalente a @BeforeEach del ejemplo Spring Boot.
    """
    event = Event.objects.create(
        name="Python Workshop",
        category=create_test_category,
        created_by=create_test_user,
        event_date=timezone.now().date(),
        status="active",
        description="A comprehensive Python workshop",
        location="Virtual",
        duration_hours=4,
        max_capacity=50,
    )
    return event


# ============================================================================
# PRUEBAS DE INTEGRACIÓN
# ============================================================================


@pytest.mark.django_db
@pytest.mark.integration
class TestEventRepositoryIntegration:
    """
    Suite de pruebas de integración para el repositorio de Events.
    
    Utiliza una base de datos PostgreSQL real en Docker (Testcontainers).
    Todas las pruebas se ejecutan en transacciones aisladas.
    
    Equivalente a la clase ICategoriaRepositoryTest del ejemplo Spring Boot.
    """
    
    def setup_method(self):
        """Se ejecuta antes de cada test individual."""
        logger.info(f"\n{'='*80}")
        logger.info(f"Iniciando test: {self._testMethodName if hasattr(self, '_testMethodName') else 'test'}")
        logger.info(f"{'='*80}")
    
    def teardown_method(self):
        """Se ejecuta después de cada test individual."""
        logger.info("Test completado\n")
    
    # ========================================================================
    # PRUEBAS DE CREACIÓN (SAVE)
    # ========================================================================
    
    def test_save_event_persists_and_assigns_id(self, create_test_event):
        """
        Prueba 1: Guardar evento - debe persistir y asignar ID generado
        
        Equivalente a: testGuardarCategoria_PersisteCategoriaConIdGenerado()
        
        Verifica que:
        - El evento se guarde correctamente en la BD
        - Se asigne un ID único (BigAutoField)
        - Los datos se persistan correctamente
        """
        assert create_test_event.id is not None
        assert create_test_event.id > 0
        assert create_test_event.name == "Python Workshop"
        assert create_test_event.status == "active"
        
        logger.info(f"✓ Evento creado con ID: {create_test_event.id}")
    
    @pytest.mark.parametrize(
        "event_name,status,capacity",
        [
            ("Django Mastery", "active", 30),
            ("FastAPI Workshop", "draft", 25),
            ("GraphQL Tutorial", "active", 40),
            ("REST API Design", "finished", 50),
            ("Microservices Architecture", "active", 100),
        ],
        ids=[
            "django-event",
            "fastapi-event",
            "graphql-event",
            "rest-event",
            "microservices-event"
        ]
    )
    def test_save_event_with_different_names_and_status(
        self,
        create_test_user,
        create_test_category,
        event_name: str,
        status: str,
        capacity: int
    ):
        """
        Prueba 2: Guardar eventos con múltiples nombres y estatus
        
        Equivalente a: @ParameterizedTest y @ValueSource del ejemplo Spring Boot
        
        Prueba que se pueden crear eventos con:
        - Diferentes nombres
        - Diferentes estatus
        - Diferentes capacidades máximas
        """
        event = Event.objects.create(
            name=event_name,
            category=create_test_category,
            created_by=create_test_user,
            event_date=timezone.now().date(),
            status=status,
            max_capacity=capacity,
        )
        
        assert event.id is not None
        assert event.name == event_name
        assert event.status == status
        assert event.max_capacity == capacity
        
        logger.info(f"✓ Evento '{event_name}' creado con estatus '{status}' y capacidad {capacity}")
    
    # ========================================================================
    # PRUEBAS DE BÚSQUEDA (FINDBYID)
    # ========================================================================
    
    def test_find_event_by_id_returns_existing_event(self, create_test_event):
        """
        Prueba 3: Buscar evento por ID - retorna evento existente
        
        Equivalente a: testFindById_RetornaCategoriaExistente()
        """
        retrieved_event = Event.objects.get(id=create_test_event.id)
        
        assert retrieved_event.id == create_test_event.id
        assert retrieved_event.name == "Python Workshop"
        assert retrieved_event.status == "active"
        
        logger.info(f"✓ Evento encontrado: {retrieved_event.name}")
    
    def test_find_event_by_id_nonexistent_raises_error(self):
        """
        Prueba 4: Buscar evento por ID inexistente - lanza excepción
        
        Equivalente a: testFindById_RetornaVacioCuandoNoExiste()
        """
        from django.core.exceptions import ObjectDoesNotExist
        
        with pytest.raises(ObjectDoesNotExist):
            Event.objects.get(id=9999)
        
        logger.info("✓ Excepción lanzada correctamente al buscar ID inexistente")
    
    # ========================================================================
    # PRUEBAS DE LISTADO (FINDALL)
    # ========================================================================
    
    def test_find_all_events_returns_all_created_events(
        self,
        create_test_event,
        create_test_user,
        create_test_category
    ):
        """
        Prueba 5: Listar eventos - retorna todos los eventos guardados
        
        Equivalente a: testFindAll_RetornaTodasLasCategorias()
        """
        # Crear eventos adicionales
        Event.objects.create(
            name="JavaScript Basics",
            category=create_test_category,
            created_by=create_test_user,
            event_date=timezone.now().date(),
            status="active",
        )
        
        Event.objects.create(
            name="React Advanced",
            category=create_test_category,
            created_by=create_test_user,
            event_date=timezone.now().date(),
            status="draft",
        )
        
        all_events = Event.objects.all()
        
        assert all_events.count() >= 3
        event_names = list(all_events.values_list('name', flat=True))
        assert "Python Workshop" in event_names
        assert "JavaScript Basics" in event_names
        assert "React Advanced" in event_names
        
        logger.info(f"✓ Total de eventos en BD: {all_events.count()}")
    
    def test_find_all_events_empty_list_when_no_records(self):
        """
        Prueba 6: Listar eventos - retorna lista vacía sin registros
        
        Equivalente a: testFindAll_RetornaListaVaciaSinRegistros()
        """
        # Eliminar todos los eventos
        Event.objects.all().delete()
        
        all_events = Event.objects.all()
        
        assert all_events.count() == 0
        
        logger.info("✓ Lista de eventos vacía verificada")
    
    # ========================================================================
    # PRUEBAS DE ACTUALIZACIÓN (UPDATE)
    # ========================================================================
    
    def test_update_event_persists_changes(self, create_test_event):
        """
        Prueba 7: Actualizar evento - debe persistir los nuevos datos
        
        Equivalente a: testActualizarCategoria_PersisteCambios()
        """
        original_id = create_test_event.id
        
        # Actualizar el evento
        create_test_event.name = "Python Workshop Advanced"
        create_test_event.status = "finished"
        create_test_event.save()
        
        # Recuperar de la BD para verificar persistencia
        updated_event = Event.objects.get(id=original_id)
        
        assert updated_event.name == "Python Workshop Advanced"
        assert updated_event.status == "finished"
        assert updated_event.id == original_id
        
        logger.info(f"✓ Evento actualizado: {updated_event.name} (Estatus: {updated_event.status})")
    
    @pytest.mark.parametrize(
        "new_name,new_status",
        [
            ("Python Advanced", "finished"),
            ("Python Basics", "active"),
            ("Python Expert", "draft"),
        ]
    )
    def test_update_event_with_different_values(
        self,
        create_test_event,
        new_name: str,
        new_status: str
    ):
        """
        Prueba 8: Actualizar evento con múltiples valores
        
        Verifica que se pueden actualizar eventos con diferentes combinaciones
        de nombre y estatus.
        """
        create_test_event.name = new_name
        create_test_event.status = new_status
        create_test_event.save()
        
        refreshed = Event.objects.get(id=create_test_event.id)
        
        assert refreshed.name == new_name
        assert refreshed.status == new_status
        
        logger.info(f"✓ Evento actualizado: '{new_name}' (Status: {new_status})")
    
    # ========================================================================
    # PRUEBAS DE ELIMINACIÓN (DELETE)
    # ========================================================================
    
    def test_delete_event_cannot_be_found_after_deletion(self, create_test_event):
        """
        Prueba 9: Eliminar evento - no debe encontrarse después de eliminar
        
        Equivalente a: testEliminarCategoria_NoPuedeEncontrarsePosteriormente()
        """
        event_id = create_test_event.id
        
        create_test_event.delete()
        
        deleted_event = Event.objects.filter(id=event_id).first()
        assert deleted_event is None
        
        logger.info(f"✓ Evento con ID {event_id} eliminado exitosamente")
    
    def test_delete_event_reduces_total_count(
        self,
        create_test_event,
        create_test_user,
        create_test_category
    ):
        """
        Prueba 10: Eliminar evento - el conteo total debe decrementar
        
        Equivalente a: testEliminarCategoria_ReduceConteoTotal()
        """
        # Crear un evento adicional
        Event.objects.create(
            name="Extra Event",
            category=create_test_category,
            created_by=create_test_user,
            event_date=timezone.now().date(),
        )
        
        total_before = Event.objects.count()
        create_test_event.delete()
        total_after = Event.objects.count()
        
        assert total_after == total_before - 1
        
        logger.info(f"✓ Conteo de eventos reducido de {total_before} a {total_after}")
    
    # ========================================================================
    # PRUEBAS CON RELACIONES Y FILTROS
    # ========================================================================
    
    def test_find_events_by_status_returns_filtered_results(
        self,
        create_test_user,
        create_test_category
    ):
        """
        Prueba 11: Filtrar eventos por estatus
        
        Verifica que el filtrado por estatus funciona correctamente en la BD real.
        """
        # Crear eventos con diferentes estatus
        for status in ["active", "draft", "finished"]:
            Event.objects.create(
                name=f"Event {status.capitalize()}",
                category=create_test_category,
                created_by=create_test_user,
                event_date=timezone.now().date(),
                status=status,
            )
        
        active_events = Event.objects.filter(status="active")
        draft_events = Event.objects.filter(status="draft")
        
        assert active_events.count() >= 1
        assert draft_events.count() >= 1
        assert all(e.status == "active" for e in active_events)
        
        logger.info(f"✓ Filtrado por estatus verificado: {active_events.count()} activos, {draft_events.count()} borradores")
    
    def test_find_events_by_date_range(
        self,
        create_test_user,
        create_test_category
    ):
        """
        Prueba 12: Buscar eventos por rango de fechas
        
        Verifica que el filtrado por fecha funciona correctamente.
        """
        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)
        next_week = today + timedelta(days=7)
        
        # Crear eventos en diferentes fechas
        Event.objects.create(
            name="Today Event",
            category=create_test_category,
            created_by=create_test_user,
            event_date=today,
        )
        
        Event.objects.create(
            name="Next Week Event",
            category=create_test_category,
            created_by=create_test_user,
            event_date=next_week,
        )
        
        # Filtrar eventos de hoy
        today_events = Event.objects.filter(event_date=today)
        upcoming_events = Event.objects.filter(event_date__gte=tomorrow)
        
        assert today_events.count() >= 1
        assert upcoming_events.count() >= 1
        
        logger.info(f"✓ Filtrado por fecha verificado: {today_events.count()} hoy, {upcoming_events.count()} próximos")
    
    def test_event_relationships_with_foreign_keys(
        self,
        create_test_event,
        create_test_user,
        create_test_category
    ):
        """
        Prueba 13: Relaciones de clave foránea se conservan en BD real
        
        Verifica que las relaciones M2O con User y EventCategory funcionan correctamente.
        """
        event = create_test_event
        
        assert event.created_by.id == create_test_user.id
        assert event.category.id == create_test_category.id
        assert event.created_by.email == "testuser@example.com"
        assert event.category.name == "Technology"
        
        logger.info(
            f"✓ Relaciones verificadas:\n"
            f"  - Usuario: {event.created_by.full_name}\n"
            f"  - Categoría: {event.category.name}"
        )


# ============================================================================
# PRUEBAS DE INTEGRIDAD Y VALIDACIÓN
# ============================================================================


@pytest.mark.django_db
@pytest.mark.integration
class TestEventDataIntegrity:
    """Suite de pruebas para validar integridad de datos en BD real."""
    
    def test_event_unique_constraints_enforced(
        self,
        create_test_user,
        create_test_category
    ):
        """
        Prueba que las restricciones UNIQUE de la BD se respetan.
        """
        # EventCategory tiene un nombre único
        with pytest.raises(Exception):  # IntegrityError
            EventCategory.objects.create(name="Technology")  # Ya existe de la fixture
    
    def test_event_required_fields_cannot_be_null(self, create_test_user, create_test_category):
        """
        Prueba que los campos requeridos no pueden ser nulos.
        """
        from django.db import IntegrityError
        
        with pytest.raises(IntegrityError):
            Event.objects.create(
                name=None,  # Campo requerido
                category=create_test_category,
                created_by=create_test_user,
                event_date=timezone.now().date(),
            )
    
    def test_event_timestamps_auto_generated(self, create_test_event):
        """
        Prueba que created_at y updated_at se generan automáticamente.
        """
        assert create_test_event.created_at is not None
        assert create_test_event.updated_at is not None
        assert create_test_event.created_at <= create_test_event.updated_at
        
        logger.info(
            f"✓ Timestamps verificados:\n"
            f"  - Creado: {create_test_event.created_at}\n"
            f"  - Actualizado: {create_test_event.updated_at}"
        )
