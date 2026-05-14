from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("instructors", "0003_instructor_created_by"),
    ]

    operations = [
        migrations.AddField(
            model_name="instructor",
            name="signature_image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="instructors/signatures/",
                help_text="Imagen de firma del instructor (PNG/JPG con fondo transparente recomendado)",
            ),
        ),
    ]
