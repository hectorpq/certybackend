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

from participants.models import Participant
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
        Tasa de éxito: {(self.successful/self.total_rows*100) if self.total_rows > 0 else 0:.1f}%
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
    }

    # Columnas opcionales
    OPTIONAL_COLUMNS = {
        'event_name': 'Nombre del evento (si no se pasa un evento global)',
        'phone': 'Teléfono',
        'institution': 'Institución',
        'certificate_template': 'Plantilla de certificado (nombre)',
    }

    def __init__(self, file_object: BytesIO, created_by_user: User = None, event=None, template=None):
        self.file_object = file_object
        self.created_by_user = created_by_user
        self.event = event        # Event object: si se pasa, se usa para todas las filas
        self.template = template  # Template object: si se pasa, sobrescribe la del evento
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
            logger.info("Excel cargado: %s filas", len(self.dataframe))
            
            # Paso 2: Validar estructura
            self._validate_columns()
            logger.info("Columnas validadas correctamente")
            
            # Retornar datos extraídos como lista de dicts
            data = self.dataframe.to_dict('records')
            logger.info("Preview: %s registros extraídos para edición", len(data))
            
            return data
            
        except ExcelImportError as e:
            logger.error("Error en validación: %s", str(e))
            raise
        except Exception as e:
            logger.error("Error inesperado: %s", str(e))
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
            
            logger.info("Iniciando procesamiento de %s registros", self.result.total_rows)
            
            # Procesar cada registro
            for index, record in enumerate(records):
                row_number = index + 1
                
                try:
                    # Convertir dict a Series para compatibilidad con _process_row
                    row = pd.Series(record)
                    self._process_row(row, row_number)
                except Exception as e:
                    logger.error("Error en fila %s: %s", row_number, str(e))
                    self.result.add_error(
                        row_number=row_number,
                        field='general',
                        message=str(e),
                        data=record
                    )
            
            # Log final
            logger.info("Procesamiento completado: %s/%s exitosos", self.result.successful, self.result.total_rows)
            
        except Exception as e:
            logger.error("Error en procesamiento masivo: %s", str(e))
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
            logger.error("Error en importación: %s", str(e))
            raise
        except Exception as e:
            logger.error("Error inesperado: %s", str(e))
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
        
        logger.info("Columnas validadas: %s", list(self.dataframe.columns))
    
    def _process_rows(self):
        """Procesa cada fila del DataFrame"""
        for index, row in self.dataframe.iterrows():
            row_number = index + 2  # +2 porque Excel empieza en 1 y hay encabezado
            
            try:
                self._process_row(row, row_number)
            except Exception as e:
                logger.error("Error en fila %s: %s", row_number, str(e))
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
        if not self.event and not event_name:
            raise ValueError("event_name no puede estar vacío")

        # Procesar en transacción atómica
        with transaction.atomic():
            # 1. Obtener o crear Participant
            participant = self._get_or_create_participant(full_name, email, document_id, phone)

            # 2. Obtener Event
            event_name = str(row.get('event_name', '')).strip() if not self.event else None
            event = self._get_event(event_name)

            # 3. Obtener o crear Enrollment
            self._get_or_create_enrollment(participant, event)

            # 4. Crear Certificate (pending)
            certificate = self._create_certificate(participant, event)

            # 5. Generar PDF si está en pending
            if certificate.status == 'pending':
                certificate.generate(generated_by=self.created_by_user, skip_attendance_check=True)

            # 6. Enviar por correo
            delivery_log = certificate.deliver(method='email', sent_by=self.created_by_user)
            if delivery_log.status != 'success':
                raise ValueError(f"Error al enviar correo a {participant.email}: {delivery_log.error_message}")

            # Registrar éxito
            self.result.add_success(certificate.id)
            logger.info("Fila %s: Certificado enviado a %s en %s", row_number, participant.email, event.name)
    
    def _validate_email(self, email: str) -> bool:
        """Valida formato de email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _get_or_create_participant(self, full_name: str, email: str, document_id: str, phone: str = None) -> Participant:
        """
        Obtiene o crea un Participant

        Estrategia:
        1. Buscar por document_id
        2. Si no existe por document_id, buscar por email
        3. Si tampoco existe por email, crear nuevo participante
        """
        try:
            participant = Participant.objects.get(document_id=document_id)
            if participant.email != email:
                participant.email = email
                participant.save()
                logger.info("Participant actualizado: %s", document_id)
            return participant
        except Participant.DoesNotExist:
            pass

        try:
            participant = Participant.objects.get(email=email)
            logger.info("Participant encontrado por email: %s", email)
            return participant
        except Participant.DoesNotExist:
            pass

        names = full_name.split(' ', 1)
        first_name = names[0]
        last_name = names[1] if len(names) > 1 else ''

        participant = Participant.objects.create(
            document_id=document_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            is_active=True
        )
        logger.info("Participant creado: %s", email)
        return participant
    
    def _get_event(self, event_name: str = None) -> Event:
        if self.event:
            return self.event
        if not event_name:
            raise ValueError("No se especificó un evento para esta fila")
        try:
            return Event.objects.get(name=event_name)
        except Event.DoesNotExist:
            raise ValueError(f"Evento no encontrado: '{event_name}'")
    
    def _get_or_create_enrollment(self, participant: Participant, event: Event):
        """Obtiene o crea una inscripción marcando asistencia = True"""
        from events.models import Enrollment
        enrollment, created = Enrollment.objects.get_or_create(
            participant=participant,
            event=event,
            defaults={
                'created_by': self.created_by_user,
                'attendance': True,
                'invitation_sent': False,
            }
        )
        if not created and not enrollment.attendance:
            enrollment.attendance = True
            enrollment.save()
        return enrollment

    def _create_certificate(self, participant: Participant, event: Event) -> Certificate:
        """
        Crea o obtiene un Certificate.
        Si ya existe y se provee una plantilla nueva (bulk), siempre la actualiza
        y resetea a 'pending' para que el PDF se regenere con la imagen correcta.
        """
        new_template = self.template or event.template

        certificate, created = Certificate.objects.get_or_create(
            participant=participant,
            event=event,
            defaults={
                'status': 'pending',
                'template': new_template,
                'generated_by': self.created_by_user,
                'verification_code': self._generate_verification_code(participant.id, event.id)
            }
        )

        if not created and self.template:
            # Siempre usar la imagen recién subida en bulk, aunque el certificado ya exista
            certificate.template = self.template
            certificate.status = 'pending'
            certificate.save(update_fields=['template', 'status'])
            logger.info("Plantilla actualizada en certificado existente: %s - %s", participant.email, event.name)
        elif created:
            logger.info("Certificado creado: %s - %s", participant.email, event.name)
        else:
            logger.info("Certificado ya existe (sin plantilla nueva): %s - %s", participant.email, event.name)

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
