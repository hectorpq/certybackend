"""
Servicio para importación masiva desde Excel y generación de certificados

Arquitectura limpia con:
- Validación exhaustiva
- Manejo robusto de errores
- Procesamiento resiliente (no falla todo si una fila falla)
- Logging detallado
- Preparado para escalar con miles de registros
"""

import pandas as pd
import logging
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Tuple, Optional
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
import re

from students.models import Student
from events.models import Event
from deliveries.models import DeliveryLog
from certificados.models import Certificate
from users.models import User


logger = logging.getLogger(__name__)


class ExcelImportError(Exception):
    """Excepción personalizada para errores de importación"""
    pass


class ExcelProcessingResult:
    """
    Clase para almacenar el resultado del procesamiento de Excel
    
    Atributos:
        total_rows: Total de filas procesadas
        successful: Cantidad de certificados creados exitosamente
        failed: Cantidad de filas que fallaron
        errors: Lista de errores por fila
        created_certificates: IDs de certificados creados
        summary: Resumen de procesamiento
    """
    
    def __init__(self):
        self.total_rows = 0
        self.successful = 0
        self.failed = 0
        self.errors: List[Dict] = []
        self.created_certificates: List[int] = []
        self.data_preview: List[Dict] = []
        self.processing_timestamp = datetime.now().isoformat()
    
    def add_error(self, row_number: int, field: str, message: str, data: Dict = None):
        """Registra un error de una fila específica"""
        self.errors.append({
            'row': row_number,
            'field': field,
            'message': message,
            'data': data or {},
            'timestamp': datetime.now().isoformat()
        })
        self.failed += 1
    
    def add_success(self, certificate_id: int):
        """Registra una creación exitosa"""
        self.successful += 1
        self.created_certificates.append(certificate_id)
    
    def to_dict(self) -> Dict:
        """Convierte el resultado a diccionario"""
        return {
            'processing_timestamp': self.processing_timestamp,
            'total_rows': self.total_rows,
            'successful': self.successful,
            'failed': self.failed,
            'success_rate': f"{(self.successful/self.total_rows*100):.1f}%" if self.total_rows > 0 else "0%",
            'errors': self.errors,
            'created_certificates': self.created_certificates,
            'data_preview': self.data_preview,
            'summary': self.get_summary()
        }
    
    def get_summary(self) -> str:
        """Genera un resumen textual del procesamiento"""
        summary = f"""
        RESUMEN DE IMPORTACIÓN
        ═══════════════════════════════════════
        Timestamp: {self.processing_timestamp}
        Total procesados: {self.total_rows}
        ✓ Exitosos: {self.successful}
        ✗ Fallidos: {self.failed}
        Tasa de éxito: {(self.successful/self.total_rows*100):.1f}% si self.total_rows > 0 else "0%"
        ═══════════════════════════════════════
        """
        
        if self.errors:
            summary += f"\n\nERRORES ENCONTRADOS ({len(self.errors)}):\n"
            for error in self.errors[:10]:  # Mostrar primeros 10 errores
                summary += f"  Fila {error['row']}: {error['message']}\n"
            if len(self.errors) > 10:
                summary += f"  ... y {len(self.errors)-10} errores más\n"
        
        return summary


class ExcelProcessingService:
    """
    Servicio para procesar archivos Excel y generar certificados masivamente
    
    Responsabilidades:
    - Validar estructura del Excel
    - Procesar datos fila por fila
    - Crear/actualizar estudiantes, eventos, inscripciones
    - Generar certificados
    - Registrar errores sin detener el proceso
    - Retornar resumen detallado
    """
    
    # Columnas requeridas en el Excel
    REQUIRED_COLUMNS = {
        'full_name': 'Nombre completo del estudiante',
        'email': 'Email del estudiante',
        'document_id': 'Documento de identidad (único)',
        'event_name': 'Nombre del evento',
    }
    
    # Columnas opcionales
    OPTIONAL_COLUMNS = {
        'phone': 'Teléfono',
        'institution': 'Institución',
        'certificate_template': 'Plantilla de certificado (nombre)',
    }
    
    def __init__(self, file_object: BytesIO, created_by_user: User = None):
        """
        Inicializa el servicio
        
        Args:
            file_object: Objeto BytesIO del archivo Excel
            created_by_user: Usuario que hace la importación
        """
        self.file_object = file_object
        self.created_by_user = created_by_user
        self.result = ExcelProcessingResult()
        self.dataframe = None
    
    def read_and_validate_structure(self) -> List[Dict]:
        """
        Lee el Excel y valida la estructura (columnas requeridas)
        Retorna los datos SIN procesar certificados
        
        Usado para: Preview antes de procesar
        
        Returns:
            Lista de diccionarios con los datos del Excel
            
        Raises:
            ExcelImportError si hay problemas al leer o validar
        """
        try:
            # Paso 1: Leer archivo
            self._read_excel_file()
            logger.info(f"Excel cargado: {len(self.dataframe)} filas")
            
            # Paso 2: Validar estructura
            self._validate_columns()
            logger.info("Columnas validadas correctamente")
            
            # Retornar datos extraídos como lista de dicts
            data = self.dataframe.to_dict('records')
            logger.info(f"Preview: {len(data)} registros extraídos para edición")
            
            return data
            
        except ExcelImportError as e:
            logger.error(f"Error en validación: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            raise ExcelImportError(f"Error al leer Excel: {str(e)}")
    
    def process_records(self, records: List[Dict]) -> ExcelProcessingResult:
        """
        Procesa una lista de registros (posiblemente editados) y crea certificados
        
        Usado para: Procesar datos después de edición
        
        Args:
            records: Lista de diccionarios con datos ya validados por el usuario
            
        Returns:
            ExcelProcessingResult con el resumen del procesamiento
        """
        try:
            self.result.total_rows = len(records)
            
            logger.info(f"Iniciando procesamiento de {self.result.total_rows} registros")
            
            # Procesar cada registro
            for index, record in enumerate(records):
                row_number = index + 1
                
                try:
                    # Convertir dict a Series para compatibilidad con _process_row
                    row = pd.Series(record)
                    self._process_row(row, row_number)
                except Exception as e:
                    logger.error(f"Error en fila {row_number}: {str(e)}")
                    self.result.add_error(
                        row_number=row_number,
                        field='general',
                        message=str(e),
                        data=record
                    )
            
            # Log final
            logger.info(f"Procesamiento completado: {self.result.successful}/{self.result.total_rows} exitosos")
            
        except Exception as e:
            logger.error(f"Error en procesamiento masivo: {str(e)}")
            raise ExcelImportError(f"Error al procesar registros: {str(e)}")
        
        return self.result
    
    def process(self) -> ExcelProcessingResult:
        """
        (Deprecated) Procesa el archivo Excel completo en una sola llamada
        Mantiene compatibilidad hacia atrás
        
        Para nuevo código, usar:
        1. read_and_validate_structure() - obtener datos
        2. process_records(data) - procesar datos
        
        Returns:
            ExcelProcessingResult con el resumen del procesamiento
        """
        try:
            # Leer y validar
            records = self.read_and_validate_structure()
            
            # Procesar los registros
            return self.process_records(records)
            
        except ExcelImportError as e:
            logger.error(f"Error en importación: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            raise ExcelImportError(f"Error al procesar Excel: {str(e)}")
    
    def _read_excel_file(self):
        """Lee el archivo Excel en un DataFrame"""
        try:
            self.dataframe = pd.read_excel(self.file_object, sheet_name=0)
            
            # Limpiar espacios en blanco en nombres de columnas
            self.dataframe.columns = self.dataframe.columns.str.strip()
            
            if len(self.dataframe) == 0:
                raise ExcelImportError("El archivo Excel está vacío")
            
            self.result.total_rows = len(self.dataframe)
            
        except pd.errors.EmptyDataError:
            raise ExcelImportError("El archivo Excel no contiene datos")
        except Exception as e:
            raise ExcelImportError(f"Error al leer Excel: {str(e)}")
    
    def _validate_columns(self):
        """Valida que existan todas las columnas requeridas"""
        missing_columns = [
            col for col in self.REQUIRED_COLUMNS.keys() 
            if col not in self.dataframe.columns
        ]
        
        if missing_columns:
            raise ExcelImportError(
                f"Columnas faltantes: {', '.join(missing_columns)}. "
                f"Requeridas: {', '.join(self.REQUIRED_COLUMNS.keys())}"
            )
        
        logger.info(f"Columnas validadas: {list(self.dataframe.columns)}")
    
    def _process_rows(self):
        """Procesa cada fila del DataFrame"""
        for index, row in self.dataframe.iterrows():
            row_number = index + 2  # +2 porque Excel empieza en 1 y hay encabezado
            
            try:
                self._process_row(row, row_number)
            except Exception as e:
                logger.error(f"Error en fila {row_number}: {str(e)}")
                self.result.add_error(
                    row_number=row_number,
                    field='general',
                    message=str(e),
                    data=row.to_dict()
                )
    
    def _process_row(self, row: pd.Series, row_number: int):
        """
        Procesa una fila individual
        
        Flujo:
        1. Validar datos
        2. Crear/obtener Student
        3. Obtener Event
        4. Crear/obtener Enrollment
        5. Generar Certificate
        """
        
        # Extrae y limpia datos
        full_name = str(row.get('full_name', '')).strip()
        email = str(row.get('email', '')).strip().lower()
        document_id = str(row.get('document_id', '')).strip()
        event_name = str(row.get('event_name', '')).strip()
        phone = str(row.get('phone', '')).strip() if 'phone' in row else None
        
        # Validaciones individuales
        if not full_name:
            raise ValueError("full_name no puede estar vacío")
        if not email:
            raise ValueError("email no puede estar vacío")
        if not self._validate_email(email):
            raise ValueError(f"Email inválido: {email}")
        if not document_id:
            raise ValueError("document_id no puede estar vacío")
        if not event_name:
            raise ValueError("event_name no puede estar vacío")
        
        # Procesar en transacción atómica
        with transaction.atomic():
            # 1. Obtener o crear Student
            student = self._get_or_create_student(full_name, email, document_id, phone)
            
            # 2. Obtener Event
            event = self._get_event(event_name)
            
            # 3. Obtener o crear Enrollment (relación student-event)
            self._get_or_create_enrollment(student, event)
            
            # 4. Generar Certificate
            certificate = self._create_certificate(student, event)
            
            # Registrar éxito
            self.result.add_success(certificate.id)
            logger.info(f"Fila {row_number}: Certificado creado - {student.email} en {event.name}")
    
    def _validate_email(self, email: str) -> bool:
        """Valida formato de email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _get_or_create_student(self, full_name: str, email: str, document_id: str, phone: str = None) -> Student:
        """
        Obtiene o crea un Student
        
        Estrategia:
        1. Buscar por document_id (debe ser único)
        2. Si no existe, crear nuevo estudiante
        3. Si existe pero email es diferente, actualizar
        """
        try:
            # Intentar obtener por document_id
            student = Student.objects.get(document_id=document_id)
            
            # Si el email cambió, actualizar
            if student.email != email:
                student.email = email
                student.save()
                logger.info(f"Student actualizado: {document_id}")
            
            return student
            
        except Student.DoesNotExist:
            # Crear nuevo estudiante
            names = full_name.split(' ', 1)
            first_name = names[0]
            last_name = names[1] if len(names) > 1 else ''
            
            student = Student.objects.create(
                document_id=document_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                is_active=True
            )
            logger.info(f"Student creado: {email}")
            return student
    
    def _get_event(self, event_name: str) -> Event:
        """
        Obtiene un Event por nombre
        
        Nota: Si el evento no existe, lanza excepción (requiere crearse previamente)
        """
        try:
            event = Event.objects.get(name=event_name)
            return event
        except Event.DoesNotExist:
            raise ValueError(f"Evento no encontrado: '{event_name}'")
    
    def _get_or_create_enrollment(self, student: Student, event: Event):
        """
        Obtiene o crea una inscripción (relación student-event)
        
        Nota: Ajustarse al modelo real de tu proyecto
        Aquí se asume que existe una tabla de Enrollments
        """
        # Esta lógica depende de tu modelo de Enrollments
        # Por ahora retornamos None, pero se puede extender
        _student = student  # Usar parámetro para evitar warning
        _event = event  # Usar parámetro para evitar warning
        return None
    
    def _create_certificate(self, student: Student, event: Event) -> Certificate:
        """
        Crea o obtiene un Certificate
        
        Evita duplicados usando get_or_create
        """
        certificate, created = Certificate.objects.get_or_create(
            student=student,
            event=event,
            defaults={
                'status': 'pending',
                'generated_by': self.created_by_user,
                'verification_code': self._generate_verification_code(student.id, event.id)
            }
        )
        
        if created:
            logger.info(f"Certificado creado: {student.email} - {event.name}")
        else:
            logger.info(f"Certificado ya existe: {student.email} - {event.name}")
        
        return certificate
    
    def _generate_verification_code(self, student_id: int, event_id: int) -> str:
        """Genera un código de verificación único"""
        import hashlib
        data = f"{student_id}-{event_id}-{datetime.now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:12].upper()
    
    @staticmethod
    def validate_file(file_object: BytesIO) -> Tuple[bool, str]:
        """
        Valida que un archivo sea Excel válido
        
        Returns:
            (is_valid: bool, message: str)
        """
        try:
            df = pd.read_excel(file_object, sheet_name=0)
            
            if len(df) == 0:
                return False, "El archivo Excel está vacío"
            
            required_cols = ExcelProcessingService.REQUIRED_COLUMNS.keys()
            missing = [col for col in required_cols if col not in df.columns]
            
            if missing:
                return False, f"Columnas faltantes: {', '.join(missing)}"
            
            return True, "Archivo válido"
            
        except Exception as e:
            return False, f"Error al validar: {str(e)}"


class BulkCertificateGeneratorService:
    """
    Servicio de alto nivel para generar certificados masivamente
    
    Coordina:
    - Importación de Excel
    - Validación de datos
    - Generación de certificados
    - Notificaciones
    """
    
    @staticmethod
    def generate_from_excel(excel_file, user: User) -> ExcelProcessingResult:
        """Genera certificados desde un archivo Excel"""
        service = ExcelProcessingService(excel_file, created_by_user=user)
        return service.process()
