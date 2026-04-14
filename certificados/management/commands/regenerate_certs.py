from django.core.management.base import BaseCommand
from django.db.models import Q
from certificados.models import Certificate
from users.models import User

class Command(BaseCommand):
    help = 'Regenerate certificates with real PDFs and send emails'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('REGENERAR TODOS LOS CERTIFICADOS'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

        # Obtener admin
        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            self.stdout.write(self.style.ERROR('❌ No hay usuario admin'))
            return

        self.stdout.write(f'✓ Admin: {admin.email}\n')

        # Obtener certificados sin PDF válido o con URL vieja
        bad_certs = Certificate.objects.select_related('student', 'event').filter(
            Q(pdf_url='') | 
            Q(pdf_url__startswith='https://example.com') |
            Q(pdf_url__startswith='https://certificates.example.com')
        )
        
        self.stdout.write(f'[1] Certificados a regenerar: {bad_certs.count()}\n')

        count = 0
        for cert in bad_certs:
            count += 1
            self.stdout.write(f'[{count}] {cert.student.first_name} - {cert.event.name}')

            # Resetear
            cert.status = 'pending'
            cert.pdf_url = ''
            cert.save()

            try:
                # Generar PDF real
                cert = cert.generate(generated_by=admin)

                # Enviar email CON PDF ADJUNTADO
                delivery_log = cert.deliver(
                    method='email',
                    recipient=cert.student.email,
                    sent_by=admin
                )

                if delivery_log.status == 'success':
                    self.stdout.write(self.style.SUCCESS(
                        f'    ✅ Email enviado a {cert.student.email} - PDF ADJUNTADO'
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        f'    ⚠️  Error: {delivery_log.error_message}'
                    ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    ❌ Error: {e}'))

        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('✅ COMPLETADO'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
        self.stdout.write('Revisa tu inbox - los PDFs deben estar ADJUNTADOS\n')
