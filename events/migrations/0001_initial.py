import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("certificados", "0001_initial"),
        ("instructors", "0003_instructor_created_by"),
        ("participants", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="EventCategory",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=100, unique=True)),
                ("description", models.TextField(blank=True)),
            ],
            options={
                "ordering": ["name"],
                "verbose_name_plural": "Event Categories",
            },
        ),
        migrations.CreateModel(
            name="Event",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("event_date", models.DateField()),
                ("end_date", models.DateField(blank=True, null=True)),
                ("duration_hours", models.IntegerField(blank=True, null=True)),
                ("location", models.CharField(blank=True, max_length=200)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("active", "Active"),
                            ("finished", "Finished"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="active",
                        max_length=20,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("auto_send_certificates", models.BooleanField(default=False)),
                ("invitation_message", models.TextField(blank=True, default="")),
                ("is_public", models.BooleanField(default=False)),
                ("max_capacity", models.IntegerField(blank=True, null=True)),
                ("name_font_size", models.IntegerField(default=24)),
                ("name_x", models.IntegerField(default=100)),
                ("name_y", models.IntegerField(default=150)),
                (
                    "template_image",
                    models.CharField(blank=True, default="", max_length=100),
                ),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="events",
                        to="events.eventcategory",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_events",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "instructor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="events",
                        to="instructors.instructor",
                    ),
                ),
                (
                    "template",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="certificados.template",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-event_date"],
                "indexes": [
                    models.Index(fields=["status"], name="event_status_idx"),
                    models.Index(fields=["event_date"], name="event_date_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="EventInstructor",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("role", models.CharField(default="principal", max_length=50)),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="event_instructors",
                        to="events.event",
                    ),
                ),
                (
                    "instructor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="event_instructor_roles",
                        to="instructors.instructor",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="event_instructors",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Event Instructor",
                "verbose_name_plural": "Event Instructors",
            },
        ),
        migrations.AddConstraint(
            model_name="eventinstructor",
            constraint=models.UniqueConstraint(
                fields=["event", "instructor"], name="unique_event_instructor"
            ),
        ),
        migrations.CreateModel(
            name="EventInvitation",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("email", models.EmailField()),
                (
                    "token",
                    models.CharField(default=uuid.uuid4, max_length=64, unique=True),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pendiente"),
                            ("sent", "Enviada"),
                            ("accepted", "Aceptada"),
                            ("rejected", "Rechazada"),
                            ("expired", "Expirada"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("responded_at", models.DateTimeField(blank=True, null=True)),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="invitations",
                        to="events.event",
                    ),
                ),
                (
                    "participant",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="event_invitations",
                        to="participants.participant",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="sent_invitations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["token"], name="invitation_token_idx"),
                    models.Index(fields=["status"], name="invitation_status_idx"),
                    models.Index(
                        fields=["email", "event"], name="invitation_email_event_idx"
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="Enrollment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("confirmed", "Confirmed"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("invitation_sent", models.BooleanField(default=False)),
                ("certificate_sent", models.BooleanField(default=False)),
                ("certificate_sent_at", models.DateTimeField(blank=True, null=True)),
                (
                    "certificate_sent_method",
                    models.CharField(blank=True, default="", max_length=20),
                ),
                ("enrolled_at", models.DateTimeField(auto_now_add=True)),
                ("attendance", models.BooleanField(default=False)),
                (
                    "grade",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=5, null=True
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                (
                    "participant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="enrollments",
                        to="participants.participant",
                    ),
                ),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="enrollments",
                        to="events.event",
                    ),
                ),
                (
                    "invitation",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="enrollments",
                        to="events.eventinvitation",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="enrollments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["enrolled_at"],
                "indexes": [
                    models.Index(
                        fields=["participant", "event"],
                        name="enrollment_participant_event_idx",
                    ),
                    models.Index(
                        fields=["attendance"], name="enrollment_attendance_idx"
                    ),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="enrollment",
            constraint=models.UniqueConstraint(
                fields=["participant", "event"], name="unique_participant_event"
            ),
        ),
    ]
