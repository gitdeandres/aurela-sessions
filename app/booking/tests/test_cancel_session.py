from datetime import timedelta

import pytest
from django.utils import timezone
from model_bakery import baker

from app.booking.exceptions import CancellationNotAllowedError
from app.booking.models import (CancellationType, CancelledBy, Session,
                                SessionStatus)


@pytest.fixture
def therapist():
    return baker.make('booking.Therapist')


@pytest.fixture
def patient():
    return baker.make('booking.Patient')


@pytest.fixture
def pending_session(therapist, patient):
    """A pending session scheduled 3 days from now."""
    return baker.make(
        'booking.Session',
        therapist=therapist,
        patient=patient,
        start_time=timezone.now() + timedelta(days=3),
        duration_minutes=60,
        status=SessionStatus.PENDING,
    )


@pytest.fixture
def confirmed_session_with_notice(therapist, patient):
    """A confirmed session scheduled far enough ahead to allow standard cancellation."""
    return baker.make(
        'booking.Session',
        therapist=therapist,
        patient=patient,
        start_time=timezone.now() + timedelta(days=3),
        duration_minutes=60,
        status=SessionStatus.CONFIRMED,
    )


@pytest.fixture
def confirmed_session_without_notice(therapist, patient):
    """A confirmed session scheduled within the cancellation notice window (2 hours away)."""
    return baker.make(
        'booking.Session',
        therapist=therapist,
        patient=patient,
        start_time=timezone.now() + timedelta(hours=2),
        duration_minutes=60,
        status=SessionStatus.CONFIRMED,
    )


@pytest.mark.django_db
class TestCancelSession:

    def test_cancel_pending_session_success(self, pending_session):
        """A pending session can be cancelled without notice restrictions."""
        from app.booking.services import cancel_session

        session = cancel_session(
            session_id=pending_session.pk,
            cancelled_by=CancelledBy.PATIENT,
            cancellation_type=CancellationType.STANDARD,
            reason='Schedule conflict',
        )

        assert session.status == SessionStatus.CANCELLED
        assert session.cancelled_by == CancelledBy.PATIENT
        assert session.cancellation_type == CancellationType.STANDARD

    def test_cancel_confirmed_session_with_enough_notice(self, confirmed_session_with_notice):
        """A confirmed session can be cancelled with sufficient advance notice."""
        from app.booking.services import cancel_session

        session = cancel_session(
            session_id=confirmed_session_with_notice.pk,
            cancelled_by=CancelledBy.PATIENT,
            cancellation_type=CancellationType.STANDARD,
            reason='Schedule conflict',
        )

        assert session.status == SessionStatus.CANCELLED

    def test_cancel_confirmed_session_patient_without_notice_fails(
        self, confirmed_session_without_notice
    ):
        """Standard patient cancellation fails within the 24h notice window."""
        from app.booking.services import cancel_session

        with pytest.raises(CancellationNotAllowedError):
            cancel_session(
                session_id=confirmed_session_without_notice.pk,
                cancelled_by=CancelledBy.PATIENT,
                cancellation_type=CancellationType.STANDARD,
            )

    def test_cancel_confirmed_session_therapist_without_notice_fails(
        self, confirmed_session_without_notice
    ):
        """Standard therapist cancellation fails within the 48h notice window."""
        from app.booking.services import cancel_session

        with pytest.raises(CancellationNotAllowedError):
            cancel_session(
                session_id=confirmed_session_without_notice.pk,
                cancelled_by=CancelledBy.THERAPIST,
                cancellation_type=CancellationType.STANDARD,
            )

    def test_cancel_emergency_bypasses_notice_window(self, confirmed_session_without_notice):
        """Emergency cancellations bypass notice requirements regardless of timing."""
        from app.booking.services import cancel_session

        session = cancel_session(
            session_id=confirmed_session_without_notice.pk,
            cancelled_by=CancelledBy.PATIENT,
            cancellation_type=CancellationType.EMERGENCY,
            reason='mental_health_crisis',
        )

        assert session.status == SessionStatus.CANCELLED
        assert session.cancellation_type == CancellationType.EMERGENCY

    def test_cancel_completed_session_fails(self, therapist, patient):
        """A completed session cannot be cancelled."""
        from app.booking.services import cancel_session

        completed_session = baker.make(
            'booking.Session',
            therapist=therapist,
            patient=patient,
            start_time=timezone.now() + timedelta(days=1),
            duration_minutes=60,
            status=SessionStatus.COMPLETED,
        )

        with pytest.raises(CancellationNotAllowedError):
            cancel_session(
                session_id=completed_session.pk,
                cancelled_by=CancelledBy.PATIENT,
                cancellation_type=CancellationType.STANDARD,
            )

    def test_cancel_already_cancelled_session_fails(self, therapist, patient):
        """A session that is already cancelled cannot be cancelled again."""
        from app.booking.services import cancel_session

        cancelled_session = baker.make(
            'booking.Session',
            therapist=therapist,
            patient=patient,
            start_time=timezone.now() + timedelta(days=1),
            duration_minutes=60,
            status=SessionStatus.CANCELLED,
        )

        with pytest.raises(CancellationNotAllowedError):
            cancel_session(
                session_id=cancelled_session.pk,
                cancelled_by=CancelledBy.PATIENT,
                cancellation_type=CancellationType.STANDARD,
            )

    def test_cancel_session_already_started_fails(self, therapist, patient):
        """A session that has already started cannot be cancelled."""
        from app.booking.services import cancel_session

        started_session = baker.make(
            'booking.Session',
            therapist=therapist,
            patient=patient,
            start_time=timezone.now() - timedelta(minutes=30),
            duration_minutes=60,
            status=SessionStatus.CONFIRMED,
        )

        with pytest.raises(CancellationNotAllowedError):
            cancel_session(
                session_id=started_session.pk,
                cancelled_by=CancelledBy.PATIENT,
                cancellation_type=CancellationType.STANDARD,
            )

    def test_cancel_session_not_found(self):
        """Cancellation fails when the session does not exist."""
        from app.booking.services import cancel_session

        with pytest.raises(Session.DoesNotExist):
            cancel_session(
                session_id=999,
                cancelled_by=CancelledBy.PATIENT,
                cancellation_type=CancellationType.STANDARD,
            )

    def test_cancel_emergency_with_invalid_reason_fails(self, confirmed_session_without_notice):
        """Emergency cancellation fails when the reason is not a recognised emergency."""
        from app.booking.serializers import CancelSessionSerializer

        serializer = CancelSessionSerializer(data={
            'cancelled_by': CancelledBy.PATIENT,
            'cancellation_type': CancellationType.EMERGENCY,
            'reason': 'no tengo ganas',
        })

        assert not serializer.is_valid()
        assert 'reason' in serializer.errors
