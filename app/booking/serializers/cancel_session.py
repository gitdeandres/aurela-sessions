from rest_framework import serializers

from app.booking.models import CancelledBy


class CancelSessionSerializer(serializers.Serializer):
    cancelled_by = serializers.ChoiceField(choices=CancelledBy.choices)
    reason = serializers.CharField(required=False, allow_blank=True, default=None)
