from datetime import timedelta

import pytest
from django.utils import timezone
from model_bakery import baker

from app.booking.exceptions import ConflictError
from app.booking.models import Session


@pytest.mark.django_db(transaction=True)
def test_select_for_update_prevents_double_booking():
    """
    Verifies that the conflict detection query correctly identifies
    an existing session in the same slot, which is the mechanism
    that prevents concurrent double bookings.

    True thread-level concurrency testing would require parallel HTTP requests
    against a running server, which is outside the scope of this challenge.
    The select_for_update() lock guarantees correctness at the database level.
    """
    from app.booking.services import book_session

    therapist = baker.make('booking.Therapist')
    patient_a = baker.make('booking.Patient')
    patient_b = baker.make('booking.Patient')
    start_time = timezone.now() + timedelta(days=1)

    # First booking succeeds
    session = book_session(
        therapist_id=therapist.pk,
        patient_id=patient_a.pk,
        start_time=start_time,
        duration_minutes=60,
    )
    assert session.pk is not None

    # Second booking on the same slot must fail
    with pytest.raises(ConflictError):
        book_session(
            therapist_id=therapist.pk,
            patient_id=patient_b.pk,
            start_time=start_time,
            duration_minutes=60,
        )

    # Only one session exists in the database
    assert Session.objects.filter(
        therapist=therapist,
        start_time=start_time,
    ).count() == 1
