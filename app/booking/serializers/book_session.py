from django.utils import timezone
from rest_framework import serializers

from app.booking.models import Patient, Therapist


class BookSessionSerializer(serializers.Serializer):
    therapist_id = serializers.IntegerField()
    patient_id = serializers.IntegerField()
    start_time = serializers.DateTimeField()
    duration_minutes = serializers.IntegerField(default=60, min_value=30, max_value=180)

    def validate_therapist_id(self, value):
        if not Therapist.objects.filter(pk=value).exists():
            raise serializers.ValidationError(
                f"Therapist with id {value} does not exist."
            )
        return value

    def validate_patient_id(self, value):
        if not Patient.objects.filter(pk=value).exists():
            raise serializers.ValidationError(
                f"Patient with id {value} does not exist."
            )
        return value

    def validate_start_time(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError(
                "Session start time must be in the future."
            )
        return value
