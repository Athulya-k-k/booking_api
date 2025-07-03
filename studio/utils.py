# fitnessbooking/utils.py

from django.utils import timezone
from django.utils.timezone import make_aware, is_naive
from django.db import transaction
from datetime import datetime
from .models import Booking


def parse_datetime_from_form(date_str, time_str):
    """
    Combine date and time strings into a timezone-aware datetime object.
    """
    datetime_str = f"{date_str} {time_str}"
    parsed = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
    return make_aware(parsed) if is_naive(parsed) else parsed


def is_valid_future_datetime(class_datetime):
    """
    Ensure datetime is in the future.
    """
    return class_datetime > timezone.now()


def create_booking(user, fitness_class):
    """
    Create a booking and decrement available slots.
    """
    Booking.objects.create(
        fitness_class=fitness_class,
        client_name=user.username,
        client_email=user.email
    )
    fitness_class.available_slots -= 1
    fitness_class.save()


def cancel_user_booking(booking):
    """
    Cancel a booking and increment available slots.
    """
    fitness_class = booking.fitness_class
    fitness_class.available_slots += 1
    fitness_class.save()
    booking.delete()


def create_booking_safe(user, fitness_class):
    """
    Safely create a booking using select_for_update to prevent overbooking.
    """
    from .models import FitnessClass  # local import to avoid circular import

    with transaction.atomic():
        cls = FitnessClass.objects.select_for_update().get(pk=fitness_class.id)

        if cls.available_slots <= 0:
            raise ValueError("No slots available for this class.")

        if cls.datetime < timezone.now():
            raise ValueError("This class has already started.")

        Booking.objects.create(
            fitness_class=cls,
            client_name=user.username,
            client_email=user.email
        )
        cls.available_slots -= 1
        cls.save()