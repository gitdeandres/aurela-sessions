from django.core.management.base import BaseCommand

from app.booking.models import Patient, Therapist

THERAPISTS = [
    {
        'name': 'Dra. Ana García',
        'email': 'ana.garcia@aurela.health',
        'speciality': 'Ansiedad y estrés',
    },
    {
        'name': 'Dr. Carlos Méndez',
        'email': 'carlos.mendez@aurela.health',
        'speciality': 'Depresión',
    },
    {
        'name': 'Dra. Laura Sánchez',
        'email': 'laura.sanchez@aurela.health',
        'speciality': 'Terapia de pareja',
    },
]

PATIENTS = [
    {
        'name': 'Andrés Ravelo',
        'email': 'andres@email.com',
    },
    {
        'name': 'Clara Martínez',
        'email': 'clara@email.com',
    },
    {
        'name': 'Diego López',
        'email': 'diego@email.com',
    },
]


class Command(BaseCommand):
    help = 'Seed the database with initial development data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding development data...')

        therapist_count = 0
        for data in THERAPISTS:
            _, created = Therapist.objects.get_or_create(
                email=data['email'],
                defaults={
                    'name': data['name'],
                    'speciality': data['speciality'],
                },
            )
            if created:
                therapist_count += 1
                self.stdout.write(f'  + Therapist created: {data["name"]}')

        patient_count = 0
        for data in PATIENTS:
            _, created = Patient.objects.get_or_create(
                email=data['email'],
                defaults={'name': data['name']},
            )
            if created:
                patient_count += 1
                self.stdout.write(f'  + Patient created: {data["name"]}')

        if therapist_count == 0 and patient_count == 0:
            self.stdout.write('  No new records — data already exists.')

        self.stdout.write(self.style.SUCCESS(
            f'Done. {therapist_count} therapist(s) and {patient_count} patient(s) created.'
        ))
