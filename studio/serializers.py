from rest_framework import serializers
from .models import FitnessClass, Booking
from django.utils import timezone


class FitnessClassSerializer(serializers.ModelSerializer):
    """Serializer for listing available fitness classes."""

    datetime = serializers.DateTimeField(format="%Y-%m-%d %H:%M", read_only=True)

    class Meta:
        model = FitnessClass
        fields = ['id', 'name', 'instructor', 'datetime', 'available_slots']


class BookingSerializer(serializers.ModelSerializer):
    """Serializer to show booking information."""

    fitness_class = FitnessClassSerializer(read_only=True)
    booked_at = serializers.DateTimeField(source='created_at', format="%d-%m-%Y", read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'fitness_class', 'client_name', 'client_email', 'booked_at']


class CreateBookingSerializer(serializers.Serializer):
    """
    Serializer used for creating a new booking via API.
    Takes class_id, and uses current user’s email internally.
    """

    class_id = serializers.IntegerField()
    client_name = serializers.CharField(max_length=100)
   

    def validate_class_id(self, value):
        from .models import FitnessClass
        try:
            cls = FitnessClass.objects.get(pk=value)
        except FitnessClass.DoesNotExist:
            raise serializers.ValidationError("Fitness class not found.")

        if cls.datetime < timezone.now():
            raise serializers.ValidationError("Cannot book a class that has already started.")

        if cls.available_slots <= 0:
            raise serializers.ValidationError("No slots available for this class.")

        return value
