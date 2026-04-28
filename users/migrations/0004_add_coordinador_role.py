from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0003_remove_null_from_email_app_password"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("admin", "Admin"),
                    ("coordinador", "Coordinador"),
                    ("participante", "Participante"),
                ],
                default="participante",
                max_length=20,
            ),
        ),
    ]
