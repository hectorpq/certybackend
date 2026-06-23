from django.utils import timezone
from datetime import timedelta
from users.models import User
from participants.models import Participant
from events.models import Event, Enrollment
from instructors.models import Instructor
from certificados.models import Certificate, Template
from services.email_service import EmailService

admin_user = User.objects.get(email="admin@certypro.com")
instructor = Instructor.objects.first()
template = Template.objects.first()

participant, created = Participant.objects.get_or_create(
    email="rrickquispe@gmail.com",
    defaults={
        "document_id": "RRICK-001",
        "first_name": "Rick",
        "last_name": "Quispe",
        "created_by": admin_user,
    },
)
print(f"Participant #{participant.id} {'created' if created else 'exists'}: {participant.first_name} {participant.last_name}")

event = Event.objects.create(
    name="Evento Test - Rick Quispe",
    status="active",
    event_date=timezone.now().date(),
    end_date=timezone.now().date() + timedelta(days=1),
    created_by=admin_user,
    instructor=instructor,
    template=template,
)
print(f"Event #{event.id} created")

enrollment = Enrollment.objects.create(event=event, participant=participant, attendance=True)
print(f"Enrollment #{enrollment.id} created")

cert = Certificate.objects.create(
    participant=participant, event=event, template=template,
    status="pending", generated_by=admin_user,
)
cert.generate(generated_by=admin_user, skip_attendance_check=True)
print(f"Certificate #{cert.id} status={cert.status}")

result = EmailService.send_certificate(cert, "rrickquispe@gmail.com")
print(f"Email result: {result}")
