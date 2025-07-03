# fitnessapp/api/urls.py
from django.urls import path
from studio.api.views import (
    FitnessClassListAPIView,
    CreateBookingAPIView,
    MyBookingsAPIView
)

urlpatterns = [
    path('classes/', FitnessClassListAPIView.as_view(), name='api_classes'),
    path('book/', CreateBookingAPIView.as_view(), name='api_create_booking'),
    path('my-bookings/', MyBookingsAPIView.as_view(), name='api_my_bookings'),
]
