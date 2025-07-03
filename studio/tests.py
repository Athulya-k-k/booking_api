from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from .models import FitnessClass, Booking


class FitnessClassModelTest(TestCase):

    def test_create_fitness_class(self):
        class_time = timezone.now() + timedelta(days=1)
        fitness_class = FitnessClass.objects.create(
            name='Yoga',
            instructor='Alice',
            datetime=class_time,
            total_slots=10,
            available_slots=10
        )
        self.assertEqual(fitness_class.name, 'Yoga')
        self.assertEqual(fitness_class.available_slots, 10)
        self.assertGreater(fitness_class.datetime, timezone.now())


class BookingModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass', email='test@example.com'
        )
        self.fitness_class = FitnessClass.objects.create(
            name='Zumba',
            instructor='Bob',
            datetime=timezone.now() + timedelta(days=2),
            total_slots=5,
            available_slots=5
        )

    def test_create_booking(self):
        booking = Booking.objects.create(
            client_name='Test User',
            client_email=self.user.email,
            fitness_class=self.fitness_class
        )
        self.assertEqual(booking.client_email, 'test@example.com')
        self.assertEqual(booking.fitness_class.name, 'Zumba')

    def test_overbooking_logic(self):
        self.fitness_class.available_slots = 0
        self.fitness_class.save()

        with self.assertRaises(Exception):
            Booking.objects.create(
                client_name='Too Late',
                client_email='late@example.com',
                fitness_class=self.fitness_class
            )
