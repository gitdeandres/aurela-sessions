from rest_framework import serializers

from app.booking.models import Session


class SessionSerializer(serializers.ModelSerializer):
    therapist_name = serializers.CharField(source='therapist.name', read_only=True)
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    end_time = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Session
        fields = [
            'id',
            'therapist',
            'therapist_name',
            'patient',
            'patient_name',
            'start_time',
            'end_time',
            'duration_minutes',
            'status',
            'cancellation_reason',
            'cancellation_type',
            'cancelled_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields
