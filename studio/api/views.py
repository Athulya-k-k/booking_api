# views/api.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from django.shortcuts import get_object_or_404

from ..models import FitnessClass, Booking
from ..serializers import (
    FitnessClassSerializer,
    BookingSerializer,
    CreateBookingSerializer
)
from ..utils import create_booking_safe

class FitnessClassListAPIView(APIView):
    """Returns all upcoming fitness classes."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        classes = FitnessClass.objects.filter(datetime__gte=timezone.now())
        serializer = FitnessClassSerializer(classes, many=True)
        return Response(serializer.data)

class CreateBookingAPIView(APIView):
    """Create a booking for a fitness class."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateBookingSerializer(data=request.data)
        if serializer.is_valid():
            class_id = serializer.validated_data['class_id']
            client_name = serializer.validated_data['client_name']
            client_email = request.user.email  # use authenticated user's email

            try:
                fitness_class = FitnessClass.objects.get(pk=class_id)
                create_booking_safe(request.user, fitness_class)
                return Response({'message': 'Booking successful'}, status=status.HTTP_201_CREATED)
            except FitnessClass.DoesNotExist:
                return Response({'error': 'Class not found'}, status=status.HTTP_404_NOT_FOUND)
            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MyBookingsAPIView(APIView):
    """List bookings for the logged-in user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        bookings = Booking.objects.filter(client_email=request.user.email)
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)
