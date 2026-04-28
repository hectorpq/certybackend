from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('certificados', '0001_initial'),
        ('events', '0001_initial'),
        ('participants', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Certificate',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('verification_code', models.CharField(max_length=50, unique=True)),
                ('pdf_url', models.TextField(blank=True)),
                ('status', models.CharField(
                    choices=[('pending', 'Pending'), ('generated', 'Generated'), ('sent', 'Sent'), ('failed', 'Failed')],
                    default='pending', max_length=20,
                )),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('issued_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('participant', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='certificates',
                    to='participants.participant',
                )),
                ('event', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='certificates',
                    to='events.event',
                )),
                ('template', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='certificates',
                    to='certificados.template',
                )),
                ('generated_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='generated_certificates',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['-issued_at'],
                'indexes': [
                    models.Index(fields=['status'], name='cert_status_idx'),
                    models.Index(fields=['verification_code'], name='cert_verif_code_idx'),
                    models.Index(fields=['participant', 'event'], name='cert_participant_event_idx'),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name='certificate',
            constraint=models.UniqueConstraint(fields=['participant', 'event'], name='unique_participant_event_cert'),
        ),
    ]
