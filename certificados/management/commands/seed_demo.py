"""
Carga datos de demostracion realistas (idempotente).

    python manage.py seed_demo          # crea / completa los datos demo
    python manage.py seed_demo --reset  # borra los datos demo y los vuelve a crear

Todos los participantes demo usan correos @demo.certypro.pe e instructores
@instructor.certypro.pe, asi se pueden identificar y borrar sin tocar datos reales.
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from certificados.models import Certificate, Template
from events.models import Enrollment, Event, EventCategory, EventInvitation
from instructors.models import Instructor
from participants.models import Participant

PARTICIPANT_DOMAIN = "demo.certypro.pe"
INSTRUCTOR_DOMAIN = "instructor.certypro.pe"
SEED = 2026

CATEGORIES = [
    ("Tecnologia", "Programacion, datos, nube e inteligencia artificial."),
    ("Gestion", "Gestion de proyectos, liderazgo y emprendimiento."),
    ("Idiomas", "Cursos y talleres de idiomas."),
    ("Salud", "Primeros auxilios, salud ocupacional y bienestar."),
    ("Educacion", "Didactica, innovacion educativa y tutoria."),
    ("Finanzas", "Finanzas personales, contabilidad y tributacion."),
]

INSTRUCTORS = [
    ("Dra. Carmen Quispe Huaman", "Ciencia de Datos e IA", "Tecnologia"),
    ("Ing. Luis Mamani Condori", "Desarrollo Web y Cloud", "Tecnologia"),
    ("Mg. Rosa Flores Vargas", "Gestion de Proyectos (PMP)", "Gestion"),
    ("Lic. Jorge Ramirez Soto", "Ingles Academico", "Idiomas"),
    ("Dr. Miguel Torres Chavez", "Salud Ocupacional", "Salud"),
    ("Mg. Patricia Rojas Medina", "Innovacion Educativa", "Educacion"),
    ("CPC. Ana Gutierrez Paredes", "Finanzas y Tributacion", "Finanzas"),
]

# (nombre, categoria, dias desde hoy, horas, aforo, publico, lugar, instructor_idx, estado)
EVENTS = [
    ("Python para Analisis de Datos", "Tecnologia", -150, 24, 50, True, "Laboratorio 3 - UPeU Juliaca", 0, "finished"),
    ("Gestion Agil de Proyectos con Scrum", "Gestion", -132, 16, 40, False, "Auditorio Central", 2, "finished"),
    ("Primeros Auxilios y RCP", "Salud", -118, 8, 60, True, "Aula Magna", 4, "finished"),
    ("Ingles para Presentaciones Academicas", "Idiomas", -104, 40, 30, False, "Virtual (Zoom)", 3, "finished"),
    (
        "Desarrollo Web con React y Django",
        "Tecnologia",
        -90,
        40,
        35,
        True,
        "Laboratorio 1 - UPeU Juliaca",
        1,
        "finished",
    ),
    ("Finanzas Personales para Profesionales", "Finanzas", -75, 8, 80, True, "Virtual (Meet)", 6, "finished"),
    ("Herramientas Digitales para el Docente", "Educacion", -61, 16, 45, False, "Aula 204", 5, "finished"),
    ("Machine Learning Aplicado", "Tecnologia", -47, 24, 40, True, "Laboratorio 3 - UPeU Juliaca", 0, "finished"),
    ("Liderazgo y Trabajo en Equipo", "Gestion", -33, 8, 70, True, "Auditorio Central", 2, "finished"),
    ("Tributacion para Emprendedores", "Finanzas", -19, 16, 50, False, "Aula 101", 6, "finished"),
    ("Seguridad en la Nube con AWS", "Tecnologia", 12, 16, 40, True, "Laboratorio 2 - UPeU Juliaca", 1, "active"),
    ("Salud Mental en el Trabajo", "Salud", 20, 8, 80, True, "Virtual (Zoom)", 4, "active"),
    ("Evaluacion por Competencias", "Educacion", 34, 16, 40, False, "Aula 204", 5, "active"),
    ("Taller de Power BI", "Tecnologia", 48, 24, 35, True, "Laboratorio 1 - UPeU Juliaca", 0, "draft"),
]

FIRST_NAMES = [
    "Alejandro",
    "Andrea",
    "Bruno",
    "Camila",
    "Carlos",
    "Daniela",
    "Diego",
    "Elena",
    "Fernando",
    "Gabriela",
    "Hector",
    "Isabel",
    "Javier",
    "Karen",
    "Luis",
    "Lucia",
    "Manuel",
    "Mariana",
    "Nicolas",
    "Natalia",
    "Oscar",
    "Paola",
    "Pedro",
    "Rocio",
    "Ricardo",
    "Sofia",
    "Sebastian",
    "Valeria",
    "Victor",
    "Ximena",
]
LAST_NAMES = [
    "Quispe",
    "Mamani",
    "Condori",
    "Huaman",
    "Flores",
    "Rojas",
    "Vargas",
    "Chavez",
    "Torres",
    "Ramirez",
    "Gutierrez",
    "Paredes",
    "Medina",
    "Soto",
    "Apaza",
    "Ccama",
    "Choque",
    "Pari",
    "Ticona",
    "Cruz",
]
N_PARTICIPANTS = 70


def _strip(s):
    return s.lower().replace(" ", "")


class Command(BaseCommand):
    help = "Carga datos de demostracion (eventos, participantes, inscripciones, certificados)."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Borra los datos demo antes de crearlos.")

    @transaction.atomic
    def handle(self, *args, **options):
        rng = random.Random(SEED)
        admin = get_user_model().objects.filter(is_superuser=True).order_by("id").first()

        if options["reset"]:
            self._reset()

        categories = {
            name: EventCategory.objects.get_or_create(name=name, defaults={"description": desc})[0]
            for name, desc in CATEGORIES
        }

        template, _ = Template.objects.get_or_create(
            name="Certificado Institucional CertyPro",
            defaults={
                "category": "General",
                "created_by": admin,
                "font_color": "#1e3a8a",
                "font_family": "Helvetica-Bold",
                "font_size": 28,
            },
        )

        instructors = []
        for full_name, specialty, _cat in INSTRUCTORS:
            slug = _strip(full_name.split(". ", 1)[-1])[:20]
            inst, _ = Instructor.objects.get_or_create(
                email=f"{slug}@{INSTRUCTOR_DOMAIN}",
                defaults={
                    "full_name": full_name,
                    "specialty": specialty,
                    "phone": f"9{rng.randint(10000000, 99999999)}",
                    "bio": f"Especialista en {specialty} con mas de 10 anios de experiencia docente.",
                    "created_by": admin,
                },
            )
            instructors.append(inst)

        participants = []
        used = set()
        for i in range(N_PARTICIPANTS):
            while True:
                fn = rng.choice(FIRST_NAMES)
                ln = f"{rng.choice(LAST_NAMES)} {rng.choice(LAST_NAMES)}"
                if (fn, ln) not in used:
                    used.add((fn, ln))
                    break
            email = f"{_strip(fn)}.{_strip(ln.split()[0])}{i + 1}@{PARTICIPANT_DOMAIN}"
            p, _ = Participant.objects.get_or_create(
                email=email,
                defaults={
                    "document_id": f"7{1000000 + i * 7919:07d}",
                    "first_name": fn,
                    "last_name": ln,
                    "phone": f"9{rng.randint(10000000, 99999999)}",
                    "created_by": admin,
                },
            )
            participants.append(p)

        # Fiabilidad latente de cada participante: hace que la asistencia tenga patron.
        reliability = {p.id: rng.betavariate(3, 1.6) for p in participants}

        today = date.today()
        counts = {"events": 0, "enrollments": 0, "certificates": 0, "invitations": 0}
        for name, cat, offset, hours, cap, public, location, inst_idx, status in EVENTS:
            ev_date = today + timedelta(days=offset)
            event, created = Event.objects.get_or_create(
                name=name,
                defaults={
                    "category": categories[cat],
                    "created_by": admin,
                    "instructor": instructors[inst_idx],
                    "description": f"{name}: programa de {hours} horas certificado por CertyPro.",
                    "event_date": ev_date,
                    "end_date": ev_date + timedelta(days=max(0, hours // 8 - 1)),
                    "duration_hours": hours,
                    "location": location,
                    "status": status,
                    "is_public": public,
                    "max_capacity": cap,
                    "template": template,
                },
            )
            counts["events"] += int(created)
            if not created:
                continue

            n_enroll = min(cap, rng.randint(18, 34)) if status != "draft" else 0
            chosen = rng.sample(participants, n_enroll)
            near_holiday = (ev_date.month, ev_date.day) in {(7, 28), (7, 29), (8, 30), (10, 8), (11, 1), (12, 8)}

            for p in chosen:
                invited = rng.random() < 0.7
                invitation = None
                if invited:
                    accepted = rng.random() < 0.75
                    invitation = EventInvitation.objects.create(
                        event=event,
                        participant=p,
                        email=p.email,
                        status="accepted" if accepted else "sent",
                        sent_at=timezone.now() - timedelta(days=max(1, -offset + rng.randint(5, 30))),
                        responded_at=timezone.now() - timedelta(days=max(1, -offset + 3)) if accepted else None,
                        expires_at=timezone.now() + timedelta(days=30),
                        created_by=admin,
                    )
                    counts["invitations"] += 1

                enrollment = Enrollment.objects.create(
                    participant=p,
                    event=event,
                    created_by=admin,
                    invitation=invitation,
                    status="confirmed" if status != "draft" else "pending",
                    invitation_sent=invited,
                )
                lead = rng.randint(0, 40)
                Enrollment.objects.filter(pk=enrollment.pk).update(
                    enrolled_at=timezone.now() + timedelta(days=offset - lead)
                )
                counts["enrollments"] += 1

                if status != "finished":
                    continue

                score = (
                    reliability[p.id]
                    + 0.012 * lead
                    - 0.008 * hours
                    + (0.15 if invitation and invitation.status == "accepted" else 0)
                    + (0.1 if public else 0)
                    - (0.3 if near_holiday else 0)
                )
                attended = rng.random() < min(0.97, max(0.1, score))
                enrollment.attendance = attended
                if attended:
                    enrollment.grade = Decimal(str(round(rng.uniform(13, 20), 1)))
                    enrollment.certificate_sent = True
                    enrollment.certificate_sent_at = timezone.now() + timedelta(days=offset + 2)
                    enrollment.certificate_sent_method = "email"
                enrollment.save()

                if attended:
                    Certificate.objects.create(
                        participant=p,
                        event=event,
                        template=template,
                        generated_by=admin,
                        status="sent",
                    )
                    counts["certificates"] += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Datos demo listos: "
                f"{len(categories)} categorias, {len(instructors)} instructores, {len(participants)} participantes, "
                f"{counts['events']} eventos nuevos, {counts['enrollments']} inscripciones, "
                f"{counts['invitations']} invitaciones, {counts['certificates']} certificados."
            )
        )

    def _reset(self):
        demo_events = Event.all_objects.filter(name__in=[e[0] for e in EVENTS])
        Certificate.all_objects.filter(event__in=demo_events).delete()
        demo_events.delete()
        Participant.all_objects.filter(email__endswith=f"@{PARTICIPANT_DOMAIN}").delete()
        Instructor.all_objects.filter(email__endswith=f"@{INSTRUCTOR_DOMAIN}").delete()
        Template.all_objects.filter(name="Certificado Institucional CertyPro").delete()
        self.stdout.write("Datos demo anteriores eliminados.")
