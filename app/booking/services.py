from datetime import timedelta
from typing import Optional

from django.db import transaction
from django.db.models import DateTimeField, ExpressionWrapper, F
from django.utils import timezone

from app.booking.exceptions import CancellationNotAllowedError, ConflictError
from app.booking.models import (TERMINAL_STATUSES, CancelledBy, Patient,
                                Session, SessionStatus, Therapist)


def book_session(
    therapist_id: int,
    patient_id: int,
    start_time,
    duration_minutes: int = 60,
) -> Session:
    """
    Books a new session between a therapist and a patient.

    Raises ConflictError if the therapist already has an overlapping session.
    Raises Therapist.DoesNotExist or Patient.DoesNotExist if either is not found.
    """
    therapist = Therapist.objects.get(pk=therapist_id)
    patient = Patient.objects.get(pk=patient_id)

    new_end_time = start_time + timedelta(minutes=duration_minutes)

    with transaction.atomic():
        # Lock active sessions for this therapist to prevent race conditions.
        # select_for_update blocks concurrent transactions from reading the
        # same rows until this transaction completes.
        active_sessions = Session.objects.select_for_update().filter(
            therapist=therapist,
            status__in=[SessionStatus.PENDING, SessionStatus.CONFIRMED],
        ).annotate(
            # Compute end_time dynamically from stored start_time + duration_minutes.
            # Avoids storing a redundant field while keeping overlap detection
            # fully within the ORM without raw SQL.
            end_time=ExpressionWrapper(
                F('start_time') + timedelta(seconds=1) * F('duration_minutes') * 60,
                output_field=DateTimeField(),
            )
        )

        # Overlap condition:
        # existing.start_time < new.end_time AND existing.end_time > new.start_time
        has_conflict = active_sessions.filter(
            start_time__lt=new_end_time,
            end_time__gt=start_time,
        ).exists()

        if has_conflict:
            raise ConflictError(
                "The therapist already has a session scheduled during this time slot."
            )

        return Session.objects.create(
            therapist=therapist,
            patient=patient,
            start_time=start_time,
            duration_minutes=duration_minutes,
        )


def cancel_session(
    session_id: int,
    cancelled_by: CancelledBy,
    reason: Optional[str] = None,
) -> Session:
    """
    Cancels an existing session if business rules allow it.

    Raises CancellationNotAllowedError if the session cannot be cancelled.
    Raises Session.DoesNotExist if the session is not found.
    """
    with transaction.atomic():
        # Lock the session row to prevent concurrent cancellation attempts
        session = Session.objects.select_for_update().get(pk=session_id)

        if not session.is_cancellable(cancelled_by):
            if session.status in TERMINAL_STATUSES:
                raise CancellationNotAllowedError(
                    f"Cannot cancel a session with status '{session.status}'."
                )
            if timezone.now() >= session.start_time:
                raise CancellationNotAllowedError(
                    "Cannot cancel a session that has already started."
                )
            raise CancellationNotAllowedError(
                "This session requires more advance notice to cancel."
            )

        session.cancel(cancelled_by=cancelled_by, reason=reason)
        return session


def get_upcoming_sessions(therapist_id: int):
    """
    Returns all upcoming active sessions for a given therapist,
    ordered by start time ascending.

    Raises Therapist.DoesNotExist if the therapist is not found.
    """
    Therapist.objects.get(pk=therapist_id)

    return Session.objects.filter(
        therapist_id=therapist_id,
        status__in=[SessionStatus.PENDING, SessionStatus.CONFIRMED],
        start_time__gt=timezone.now(),
    ).select_related('therapist', 'patient')
