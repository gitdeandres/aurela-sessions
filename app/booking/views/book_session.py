from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from app.booking.serializers import BookSessionSerializer, SessionSerializer
from app.booking.services import book_session


class BookSessionView(APIView):
    def post(self, request: Request) -> Response:
        serializer = BookSessionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        session = book_session(**serializer.validated_data)
        return Response(
            SessionSerializer(session).data,
            status=status.HTTP_201_CREATED,
        )
