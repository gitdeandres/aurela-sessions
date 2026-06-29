from datetime import timedelta

import pytest
from django.utils import timezone
from model_bakery import baker

from app.booking.exceptions import ConflictError
from app.booking.models import SessionStatus


@pytest.fixture
def therapist():
    return baker.make('booking.Therapist')


@pytest.fixture
def patient():
    return baker.make('booking.Patient')


@pytest.fixture
def future_start_time():
    return timezone.now() + timedelta(days=1)


@pytest.mark.django_db
class TestBookSession:

    def test_book_session_success(self, therapist, patient, future_start_time):
        """A session is created successfully with valid data."""
        from app.booking.services import book_session

        session = book_session(
            therapist_id=therapist.pk,
            patient_id=patient.pk,
            start_time=future_start_time,
            duration_minutes=60,
        )

        assert session.pk is not None
        assert session.therapist == therapist
        assert session.patient == patient
        assert session.status == SessionStatus.PENDING
        assert session.duration_minutes == 60

    def test_book_session_conflict_exact_overlap(self, therapist, patient, future_start_time):
        """Booking fails when a new session starts at the same time as an existing one."""
        from app.booking.services import book_session

        book_session(
            therapist_id=therapist.pk,
            patient_id=patient.pk,
            start_time=future_start_time,
            duration_minutes=60,
        )

        with pytest.raises(ConflictError):
            book_session(
                therapist_id=therapist.pk,
                patient_id=patient.pk,
                start_time=future_start_time,
                duration_minutes=60,
            )

    def test_book_session_conflict_partial_overlap(self, therapist, patient, future_start_time):
        """Booking fails when a new session partially overlaps an existing one."""
        from app.booking.services import book_session

        book_session(
            therapist_id=therapist.pk,
            patient_id=patient.pk,
            start_time=future_start_time,
            duration_minutes=60,
        )

        # Starts 30 minutes into the existing session
        with pytest.raises(ConflictError):
            book_session(
                therapist_id=therapist.pk,
                patient_id=patient.pk,
                start_time=future_start_time + timedelta(minutes=30),
                duration_minutes=60,
            )

    def test_book_session_no_conflict_adjacent(self, therapist, patient, future_start_time):
        """Booking succeeds when a new session starts exactly when the previous one ends."""
        from app.booking.services import book_session

        book_session(
            therapist_id=therapist.pk,
            patient_id=patient.pk,
            start_time=future_start_time,
            duration_minutes=60,
        )

        # Starts exactly when the first session ends — no overlap
        session = book_session(
            therapist_id=therapist.pk,
            patient_id=patient.pk,
            start_time=future_start_time + timedelta(minutes=60),
            duration_minutes=60,
        )

        assert session.pk is not None

    def test_book_session_conflict_only_for_same_therapist(self, patient, future_start_time):
        """Conflict detection is scoped to the therapist — different therapists can overlap."""
        from app.booking.services import book_session

        therapist_a = baker.make('booking.Therapist')
        therapist_b = baker.make('booking.Therapist')

        book_session(
            therapist_id=therapist_a.pk,
            patient_id=patient.pk,
            start_time=future_start_time,
            duration_minutes=60,
        )

        # Same time slot but different therapist — should succeed
        session = book_session(
            therapist_id=therapist_b.pk,
            patient_id=patient.pk,
            start_time=future_start_time,
            duration_minutes=60,
        )

        assert session.pk is not None

    def test_book_session_therapist_not_found(self, patient, future_start_time):
        """Booking fails when the therapist does not exist."""
        from app.booking.models import Therapist
        from app.booking.services import book_session

        with pytest.raises(Therapist.DoesNotExist):
            book_session(
                therapist_id=999,
                patient_id=patient.pk,
                start_time=future_start_time,
                duration_minutes=60,
            )

    def test_book_session_patient_not_found(self, therapist, future_start_time):
        """Booking fails when the patient does not exist."""
        from app.booking.models import Patient
        from app.booking.services import book_session

        with pytest.raises(Patient.DoesNotExist):
            book_session(
                therapist_id=therapist.pk,
                patient_id=999,
                start_time=future_start_time,
                duration_minutes=60,
            )

    def test_book_session_invalid_start_time(self, therapist, patient):
        """Booking fails when start_time is in the past."""
        from app.booking.serializers import BookSessionSerializer

        serializer = BookSessionSerializer(data={
            'therapist_id': therapist.pk,
            'patient_id': patient.pk,
            'start_time': (timezone.now() - timedelta(hours=1)).isoformat(),
            'duration_minutes': 60,
        })

        assert not serializer.is_valid()
        assert 'start_time' in serializer.errors
