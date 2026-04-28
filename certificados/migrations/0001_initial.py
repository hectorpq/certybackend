import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Template",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=100)),
                ("category", models.CharField(blank=True, max_length=100)),
                (
                    "background_image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to="templates/backgrounds/",
                    ),
                ),
                ("background_url", models.TextField(blank=True)),
                ("preview_url", models.TextField(blank=True)),
                ("layout_config", models.JSONField(default=dict)),
                ("is_active", models.BooleanField(default=True)),
                ("font_color", models.CharField(default="#000000", max_length=20)),
                ("font_family", models.CharField(default="Helvetica", max_length=50)),
                ("font_size", models.IntegerField(default=24)),
                ("x_coord", models.FloatField(default=100.0)),
                ("y_coord", models.FloatField(default=150.0)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="templates",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["is_active"], name="template_is_active_idx"),
                    models.Index(fields=["category"], name="template_category_idx"),
                ],
            },
        ),
    ]
