import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Patient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('email', models.EmailField(max_length=254, unique=True)),
            ],
            options={
                'db_table': 'patient',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Therapist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('speciality', models.CharField(blank=True, max_length=200)),
            ],
            options={
                'db_table': 'therapist',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sessions', to='booking.patient')),
                ('therapist', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sessions', to='booking.therapist')),
                ('start_time', models.DateTimeField()),
                ('duration_minutes', models.PositiveIntegerField(default=60)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('completed', 'Completed'), ('cancelled', 'Cancelled'), ('no_show', 'No Show')], default='pending', max_length=20)),
                ('cancelled_by', models.CharField(choices=[('patient', 'Patient'), ('therapist', 'Therapist'), ('system', 'System')], max_length=20, null=True)),
                ('cancellation_reason', models.TextField(null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'session',
                'ordering': ['start_time'],
                'indexes': [models.Index(fields=['therapist', 'start_time'], name='booking_ses_therapi_e5ba34_idx'), models.Index(fields=['status'], name='booking_ses_status_7750b9_idx')],
            },
        ),
    ]
