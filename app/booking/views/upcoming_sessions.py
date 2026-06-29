from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from app.booking.serializers import SessionSerializer
from app.booking.services import get_upcoming_sessions


class UpcomingSessionsView(APIView):
    def get(self, request: Request, pk: int) -> Response:
        sessions = get_upcoming_sessions(therapist_id=pk)
        serializer = SessionSerializer(sessions, many=True)
        return Response(serializer.data)
