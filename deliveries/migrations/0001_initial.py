from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('certificados', '0002_certificate'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DeliveryLog',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('delivery_method', models.CharField(
                    choices=[('email', 'Email'), ('whatsapp', 'WhatsApp'), ('link', 'Link')],
                    max_length=20,
                )),
                ('recipient', models.CharField(blank=True, max_length=200)),
                ('status', models.CharField(
                    choices=[('success', 'Success'), ('error', 'Error'), ('pending', 'Pending')],
                    default='pending', max_length=20,
                )),
                ('error_message', models.TextField(blank=True)),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('certificate', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='deliveries',
                    to='certificados.certificate',
                )),
                ('sent_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='deliveries_sent',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Delivery Log',
                'verbose_name_plural': 'Delivery Logs',
                'ordering': ['-sent_at'],
                'indexes': [
                    models.Index(fields=['status'], name='delivery_status_idx'),
                    models.Index(fields=['delivery_method'], name='delivery_method_idx'),
                    models.Index(fields=['certificate'], name='delivery_cert_idx'),
                ],
            },
        ),
    ]
