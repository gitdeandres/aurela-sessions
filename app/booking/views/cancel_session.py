from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from app.booking.serializers import CancelSessionSerializer, SessionSerializer
from app.booking.services import cancel_session


class CancelSessionView(APIView):
    def post(self, request: Request, pk: int) -> Response:
        serializer = CancelSessionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        session = cancel_session(
            session_id=pk,
            **serializer.validated_data,
        )
        return Response(
            SessionSerializer(session).data,
            status=status.HTTP_200_OK,
        )
