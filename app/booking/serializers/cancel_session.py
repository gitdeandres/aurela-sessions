from rest_framework import serializers

from app.booking.models import EMERGENCY_REASONS, CancellationType, CancelledBy


class CancelSessionSerializer(serializers.Serializer):
    cancelled_by = serializers.ChoiceField(choices=CancelledBy.choices)
    cancellation_type = serializers.ChoiceField(
        choices=CancellationType.choices,
        default=CancellationType.STANDARD,
    )
    reason = serializers.CharField(required=False, allow_blank=True, default=None)

    def validate(self, attrs):
        if attrs.get('cancellation_type') == CancellationType.EMERGENCY:
            if attrs.get('reason') not in EMERGENCY_REASONS:
                raise serializers.ValidationError({
                    'reason': (
                        f"Emergency cancellations require a valid reason. "
                        f"Accepted values: {', '.join(EMERGENCY_REASONS)}"
                    )
                })
        return attrs
