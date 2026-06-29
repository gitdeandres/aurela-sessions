from django.urls import path

from app.booking.views import (BookSessionView, CancelSessionView,
                               UpcomingSessionsView)

urlpatterns = [
    path('sessions/', BookSessionView.as_view(), name='book-session'),
    path('sessions/<int:pk>/cancel/', CancelSessionView.as_view(), name='cancel-session'),
    path('therapists/<int:pk>/sessions/', UpcomingSessionsView.as_view(), name='upcoming-sessions'),
]
