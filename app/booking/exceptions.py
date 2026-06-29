from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


class ConflictError(Exception):
    """Raised when a session booking conflicts with an existing schedule."""
    pass


class CancellationNotAllowedError(Exception):
    """Raised when a cancellation attempt violates business rules."""
    pass


def custom_exception_handler(exc, context):
    # Let DRF handle its own exceptions first
    response = exception_handler(exc, context)
    if response is not None:
        return response

    if isinstance(exc, ConflictError):
        return Response(
            {'error': str(exc)},
            status=status.HTTP_409_CONFLICT,
        )

    if isinstance(exc, CancellationNotAllowedError):
        return Response(
            {'error': str(exc)},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    if isinstance(exc, ObjectDoesNotExist):
        return Response(
            {'error': str(exc)},
            status=status.HTTP_404_NOT_FOUND,
        )

    return None
