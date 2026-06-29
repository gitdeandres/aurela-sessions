from datetime import timedelta

import pytest
from django.utils import timezone
from model_bakery import baker

from app.booking.models import SessionStatus


@pytest.fixture
def therapist():
    return baker.make('booking.Therapist')


@pytest.fixture
def patient():
    return baker.make('booking.Patient')


@pytest.mark.django_db
class TestUpcomingSessions:

    def test_upcoming_sessions_returns_future_active_sessions(self, therapist, patient):
        """Only future pending and confirmed sessions are returned."""
        from app.booking.services import get_upcoming_sessions

        pending = baker.make(
            'booking.Session',
            therapist=therapist,
            patient=patient,
            start_time=timezone.now() + timedelta(days=1),
            status=SessionStatus.PENDING,
        )
        confirmed = baker.make(
            'booking.Session',
            therapist=therapist,
            patient=patient,
            start_time=timezone.now() + timedelta(days=2),
            status=SessionStatus.CONFIRMED,
        )

        sessions = get_upcoming_sessions(therapist_id=therapist.pk)

        assert pending in sessions
        assert confirmed in sessions

    def test_upcoming_sessions_excludes_past_sessions(self, therapist, patient):
        """Past sessions are not returned even if their status is active."""
        from app.booking.services import get_upcoming_sessions

        baker.make(
            'booking.Session',
            therapist=therapist,
            patient=patient,
            start_time=timezone.now() - timedelta(days=1),
            status=SessionStatus.PENDING,
        )

        sessions = get_upcoming_sessions(therapist_id=therapist.pk)

        assert sessions.count() == 0

    def test_upcoming_sessions_excludes_cancelled_sessions(self, therapist, patient):
        """Cancelled sessions are not returned."""
        from app.booking.services import get_upcoming_sessions

        baker.make(
            'booking.Session',
            therapist=therapist,
            patient=patient,
            start_time=timezone.now() + timedelta(days=1),
            status=SessionStatus.CANCELLED,
        )

        sessions = get_upcoming_sessions(therapist_id=therapist.pk)

        assert sessions.count() == 0

    def test_upcoming_sessions_excludes_completed_sessions(self, therapist, patient):
        """Completed sessions are not returned."""
        from app.booking.services import get_upcoming_sessions

        baker.make(
            'booking.Session',
            therapist=therapist,
            patient=patient,
            start_time=timezone.now() + timedelta(days=1),
            status=SessionStatus.COMPLETED,
        )

        sessions = get_upcoming_sessions(therapist_id=therapist.pk)

        assert sessions.count() == 0

    def test_upcoming_sessions_scoped_to_therapist(self, patient):
        """Sessions from other therapists are not returned."""
        from app.booking.services import get_upcoming_sessions

        therapist_a = baker.make('booking.Therapist')
        therapist_b = baker.make('booking.Therapist')

        baker.make(
            'booking.Session',
            therapist=therapist_a,
            patient=patient,
            start_time=timezone.now() + timedelta(days=1),
            status=SessionStatus.PENDING,
        )

        sessions = get_upcoming_sessions(therapist_id=therapist_b.pk)

        assert sessions.count() == 0

    def test_upcoming_sessions_ordered_by_start_time(self, therapist, patient):
        """Sessions are returned in ascending order by start time."""
        from app.booking.services import get_upcoming_sessions

        second = baker.make(
            'booking.Session',
            therapist=therapist,
            patient=patient,
            start_time=timezone.now() + timedelta(days=2),
            status=SessionStatus.PENDING,
        )
        first = baker.make(
            'booking.Session',
            therapist=therapist,
            patient=patient,
            start_time=timezone.now() + timedelta(days=1),
            status=SessionStatus.PENDING,
        )

        sessions = list(get_upcoming_sessions(therapist_id=therapist.pk))

        assert sessions[0] == first
        assert sessions[1] == second

    def test_upcoming_sessions_therapist_not_found(self):
        """Raises DoesNotExist when the therapist does not exist."""
        from app.booking.models import Therapist
        from app.booking.services import get_upcoming_sessions

        with pytest.raises(Therapist.DoesNotExist):
            get_upcoming_sessions(therapist_id=999)

    def test_upcoming_sessions_empty_when_no_sessions(self, therapist):
        """Returns empty queryset when therapist has no upcoming sessions."""
        from app.booking.services import get_upcoming_sessions

        sessions = get_upcoming_sessions(therapist_id=therapist.pk)

        assert sessions.count() == 0
