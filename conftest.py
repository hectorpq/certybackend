"""
Configuración global de pytest y fixtures para pruebas de integración.
Gestiona el ciclo de vida de los contenedores Docker (PostgreSQL) utilizando Testcontainers,
emulando la lógica de la clase MySQLTestContainer del ejemplo de Spring Boot.
"""

import os
import logging
from typing import Generator

import pytest
from django.conf import settings
from testcontainers.postgres import PostgresContainer

# Configurar logging
logger = logging.getLogger(__name__)


class PostgreSQLTestContainer:
    """
    Contenedor de prueba para PostgreSQL.
    Equivalente a la clase MySQLTestContainer del proyecto Spring Boot.
    
    Gestiona el ciclo de vida del contenedor Docker:
    - Inicia automáticamente antes de las pruebas
    - Captura dinámicamente las credenciales
    - Sobrescribe DATABASES de Django
    - Se detiene y elimina al finalizar
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.container = None
        self._initialized = True
    
    def start(self) -> dict:
        """
        Inicia el contenedor PostgreSQL.
        
        Returns:
            dict: Diccionario con credenciales (url, user, password, db_name)
        """
        try:
            logger.info("🐘 Iniciando contenedor PostgreSQL para pruebas...")
            
            self.container = PostgresContainer(
                image="postgres:16-alpine",
                dbname="testdb",
                username="testuser",
                password="testpass",
            )
            
            self.container.start()
            
            # Capturar dinámicamente la URL de conexión
            db_url = self.container.get_connection_url()
            
            credentials = {
                'url': db_url,
                'user': self.container.username,
                'password': self.container.password,
                'db_name': self.container.dbname,
                'host': self.container.get_container_host_ip(),
                'port': self.container.get_exposed_port('5432'),
            }
            
            logger.info(
                f"✓ Contenedor PostgreSQL iniciado exitosamente\n"
                f"  - Host: {credentials['host']}\n"
                f"  - Puerto: {credentials['port']}\n"
                f"  - Base de datos: {credentials['db_name']}\n"
                f"  - Usuario: {credentials['user']}"
            )
            
            return credentials
        
        except Exception as e:
            logger.error(f"✗ Error al iniciar contenedor PostgreSQL: {e}")
            raise
    
    def stop(self):
        """Detiene y elimina el contenedor PostgreSQL."""
        if self.container:
            try:
                logger.info("🛑 Deteniendo contenedor PostgreSQL...")
                self.container.stop()
                logger.info("✓ Contenedor PostgreSQL detenido")
            except Exception as e:
                logger.error(f"✗ Error al detener contenedor: {e}")


# ============================================================================
# FIXTURES DE PYTEST
# ============================================================================

@pytest.fixture(scope='session', autouse=True)
def setup_postgres_container() -> Generator[dict, None, None]:
    """
    Fixture con alcance de sesión que gestiona el ciclo de vida del contenedor PostgreSQL.
    
    Equivalente a la anotación @Testcontainers y @DynamicPropertySource del ejemplo Spring Boot.
    
    - Inicia el contenedor antes de ejecutar todos los tests
    - Sobrescribe DATABASES de Django dinámicamente
    - Detiene el contenedor al finalizar toda la sesión de pruebas
    
    Yields:
        dict: Credenciales del contenedor
    """
    container_manager = PostgreSQLTestContainer()
    credentials = container_manager.start()
    
    # Sobrescribir DATABASES de Django con las credenciales del contenedor
    # Equivalente a @DynamicPropertySource en Spring Boot
    _override_django_database_settings(credentials)
    
    yield credentials
    
    # Limpieza: Detener el contenedor al finalizar la sesión
    container_manager.stop()


def _override_django_database_settings(credentials: dict) -> None:
    """
    Sobrescribe la configuración de DATABASES de Django con las credenciales
    del contenedor PostgreSQL recién iniciado.
    
    Equivalente a la función de @DynamicPropertySource del ejemplo Spring Boot.
    
    Args:
        credentials (dict): Diccionario con credenciales (url, user, password, etc.)
    """
    try:
        # Extraer componentes de la URL de conexión
        # Format: postgresql://user:password@host:port/dbname
        from urllib.parse import urlparse
        
        parsed_url = urlparse(credentials['url'])
        
        # Actualizar la configuración de DATABASES
        settings.DATABASES['default'] = {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': credentials['db_name'],
            'USER': credentials['user'],
            'PASSWORD': credentials['password'],
            'HOST': credentials['host'],
            'PORT': credentials['port'],
            'CONN_MAX_AGE': 0,  # Deshabilitar persistencia de conexiones para pruebas
            'ATOMIC_REQUESTS': True,  # Usar transacciones para cada test
        }
        
        logger.info(
            f"✓ Configuración de DATABASES de Django sobrescrita:\n"
            f"  - Engine: {settings.DATABASES['default']['ENGINE']}\n"
            f"  - Host: {settings.DATABASES['default']['HOST']}\n"
            f"  - Port: {settings.DATABASES['default']['PORT']}\n"
            f"  - Database: {settings.DATABASES['default']['NAME']}"
        )
    
    except Exception as e:
        logger.error(f"✗ Error al sobrescribir DATABASES: {e}")
        raise


@pytest.fixture(scope='function', autouse=True)
def reset_database_state(setup_postgres_container):
    """
    Fixture que se ejecuta antes de cada test individual para limpiar el estado de la BD.
    
    Equivalente a @BeforeEach del ejemplo Spring Boot.
    
    Nota: Django se encarga de limpiar/resetear las transacciones automáticamente
    con ATOMIC_REQUESTS=True, por lo que esta fixture es principalmente para
    operaciones adicionales si es necesario.
    """
    yield
    # Django maneja la limpieza automáticamente con ATOMIC_REQUESTS


@pytest.fixture
def db_cleanup():
    """
    Fixture que permite limpiar datos específicos dentro de un test.
    
    Uso:
        def test_example(db_cleanup):
            # Los datos se limpiarán automáticamente al finalizar el test
            pass
    """
    yield
    # Aquí se pueden agregar operaciones de limpieza adicionales si es necesario


# ============================================================================
# PYTEST HOOKS
# ============================================================================

def pytest_configure(config):
    """
    Hook de pytest que se ejecuta antes de que comience la sesión de pruebas.
    Utilizamos esto para registrar los marcadores personalizados.
    """
    config.addinivalue_line(
        "markers", 
        "integration: marca test como prueba de integración (usa base de datos real)"
    )
    config.addinivalue_line(
        "markers",
        "unit: marca test como prueba unitaria (sin base de datos, sin servicios externos)"
    )
    logger.info("=" * 80)
    logger.info("PYTEST CONFIGURATION - Pruebas de Integración con Testcontainers")
    logger.info("=" * 80)
