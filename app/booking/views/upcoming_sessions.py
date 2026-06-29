from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from app.booking.serializers import SessionSerializer
from app.booking.services import get_upcoming_sessions


class UpcomingSessionsView(APIView):
    def get(self, request: Request, pk: id):
        sessions = get_upcoming_sessions(therapist_id=pk)
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(sessions, request)
        return paginator.get_paginated_response(SessionSerializer(page, many=True).data)
