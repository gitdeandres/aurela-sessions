from datetime import timedelta
from typing import Optional

from django.db import models
from django.utils import timezone

from .patient import Patient
from .therapist import Therapist


class SessionStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    CONFIRMED = 'confirmed', 'Confirmed'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'
    NO_SHOW = 'no_show', 'No Show'


CANCELLABLE_STATUSES = {SessionStatus.PENDING, SessionStatus.CONFIRMED}
TERMINAL_STATUSES = {SessionStatus.COMPLETED,
                     SessionStatus.CANCELLED,
                     SessionStatus.NO_SHOW}
PATIENT_NOTICE_HOURS = 24
THERAPIST_NOTICE_HOURS = 48


class CancelledBy(models.TextChoices):
    PATIENT = 'patient', 'Patient'
    THERAPIST = 'therapist', 'Therapist'
    SYSTEM = 'system', 'System'  # reserved for future automated cancellations


class CancellationType(models.TextChoices):
    STANDARD = 'standard', 'Standard'
    EMERGENCY = 'emergency', 'Emergency'  # crisis, force majeure


EMERGENCY_REASONS = {
    'mental_health_crisis',
    'medical_emergency',
    'force_majeure',
    'bereavement',
}


class Session(models.Model):
    therapist = models.ForeignKey(
        Therapist,
        on_delete=models.PROTECT,
        related_name='sessions',
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name='sessions',
    )
    start_time = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    status = models.CharField(
        max_length=20,
        choices=SessionStatus.choices,
        default=SessionStatus.PENDING,
    )
    cancelled_by = models.CharField(
        max_length=20,
        choices=CancelledBy.choices,
        null=True,
    )
    cancellation_type = models.CharField(
        max_length=20,
        choices=CancellationType.choices,
        null=True,
    )
    cancellation_reason = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'session'
        ordering = ['start_time']
        indexes = [
            models.Index(fields=['therapist', 'start_time']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return (
            f"Session {self.pk} | "
            f"{self.therapist} → {self.patient} | "
            f"{self.start_time:%Y-%m-%d %H:%M} | "
            f"{self.status}"
        )

    @property
    def end_time(self):
        return self.start_time + timedelta(minutes=self.duration_minutes)

    def is_cancellable(
        self,
        cancelled_by: Optional[CancelledBy] = None,
        cancellation_type: CancellationType = CancellationType.STANDARD,
    ) -> bool:
        """
        A session is cancellable if:
        - Its status allows cancellation (pending or confirmed)
        - It has not started yet
        - If confirmed and standard: therapist needs 48h notice, patient 24h
        - If confirmed and emergency: no notice required, any time before start
        """
        if self.status not in CANCELLABLE_STATUSES:
            return False

        now = timezone.now()

        if now >= self.start_time:
            return False

        # Emergency cancellations bypass notice requirements
        if cancellation_type == CancellationType.EMERGENCY:
            return True

        if self.status == SessionStatus.CONFIRMED:
            hours_remaining = (self.start_time - now).total_seconds() / 3600
            notice_required = (
                THERAPIST_NOTICE_HOURS
                if cancelled_by == CancelledBy.THERAPIST
                else PATIENT_NOTICE_HOURS
            )
            if hours_remaining < notice_required:
                return False

        return True

    def cancel(
        self,
        cancelled_by: CancelledBy,
        cancellation_type: CancellationType = CancellationType.STANDARD,
        reason: str = '',
    ) -> None:
        """
        Cancel the session if business rules allow it.
        Raises ValueError if the session cannot be cancelled.
        """
        if not self.is_cancellable(cancelled_by=cancelled_by,
                                   cancellation_type=cancellation_type):
            if self.status in TERMINAL_STATUSES:
                raise ValueError(
                    f"Cannot cancel a session with status '{self.status}'."
                )
            if timezone.now() >= self.start_time:
                raise ValueError(
                    "Cannot cancel a session that has already started."
                )
            raise ValueError(
                "This session requires more advance notice to cancel."
            )

        self.status = SessionStatus.CANCELLED
        self.cancellation_reason = reason
        self.cancelled_by = cancelled_by
        self.cancellation_type = cancellation_type
        self.save(update_fields=[
            'status',
            'cancellation_reason',
            'cancelled_by',
            'cancellation_type',
            'updated_at',
        ])
