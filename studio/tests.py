from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status

from .models import FitnessClass, Booking
from .utils import create_booking_safe, cancel_user_booking, parse_datetime_from_form


class FitnessClassModelTest(TestCase):
    """Test cases for FitnessClass model."""

    def test_create_fitness_class(self):
        """Test creating a fitness class."""
        class_time = timezone.now() + timedelta(days=1)
        fitness_class = FitnessClass.objects.create(
            name='Yoga',
            instructor='Alice',
            datetime=class_time,
            total_slots=10,
            available_slots=10
        )
        self.assertEqual(fitness_class.name, 'Yoga')
        self.assertEqual(fitness_class.instructor, 'Alice')
        self.assertEqual(fitness_class.total_slots, 10)
        self.assertEqual(fitness_class.available_slots, 10)
        self.assertGreater(fitness_class.datetime, timezone.now())

    def test_fitness_class_str_representation(self):
        """Test string representation of fitness class."""
        class_time = timezone.now() + timedelta(days=1)
        fitness_class = FitnessClass.objects.create(
            name='Zumba',
            instructor='Bob',
            datetime=class_time,
            total_slots=15,
            available_slots=15
        )
        expected_str = f"Zumba on {class_time}"
        self.assertEqual(str(fitness_class), expected_str)

    def test_fitness_class_choices(self):
        """Test that only valid class types can be created."""
        valid_choices = ['Yoga', 'Zumba', 'HIIT']
        for choice in valid_choices:
            class_time = timezone.now() + timedelta(days=1)
            fitness_class = FitnessClass.objects.create(
                name=choice,
                instructor='Test Instructor',
                datetime=class_time,
                total_slots=10,
                available_slots=10
            )
            self.assertEqual(fitness_class.name, choice)


class BookingModelTest(TestCase):
    """Test cases for Booking model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass', 
            email='test@example.com'
        )
        self.fitness_class = FitnessClass.objects.create(
            name='Zumba',
            instructor='Bob',
            datetime=timezone.now() + timedelta(days=2),
            total_slots=5,
            available_slots=5
        )

    def test_create_booking(self):
        """Test creating a booking."""
        booking = Booking.objects.create(
            client_name='Test User',
            client_email=self.user.email,
            fitness_class=self.fitness_class
        )
        self.assertEqual(booking.client_email, 'test@example.com')
        self.assertEqual(booking.client_name, 'Test User')
        self.assertEqual(booking.fitness_class.name, 'Zumba')
        self.assertIsNotNone(booking.created_at)

    def test_booking_str_representation(self):
        """Test string representation of booking."""
        booking = Booking.objects.create(
            client_name='Test User',
            client_email=self.user.email,
            fitness_class=self.fitness_class
        )
        expected_str = f"Test User - Zumba"
        self.assertEqual(str(booking), expected_str)

    def test_booking_related_name(self):
        """Test that bookings can be accessed via fitness_class.bookings."""
        booking = Booking.objects.create(
            client_name='Test User',
            client_email=self.user.email,
            fitness_class=self.fitness_class
        )
        self.assertEqual(self.fitness_class.bookings.count(), 1)
        self.assertEqual(self.fitness_class.bookings.first(), booking)


class UtilsTest(TestCase):
    """Test cases for utility functions."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            email='test@example.com'
        )
        self.fitness_class = FitnessClass.objects.create(
            name='Yoga',
            instructor='Alice',
            datetime=timezone.now() + timedelta(days=1),
            total_slots=3,
            available_slots=3
        )

    def test_parse_datetime_from_form(self):
        """Test parsing datetime from form inputs."""
        date_str = "2025-07-10"
        time_str = "14:30"
        result = parse_datetime_from_form(date_str, time_str)
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 7)
        self.assertEqual(result.day, 10)
        self.assertEqual(result.hour, 14)
        self.assertEqual(result.minute, 30)

    def test_create_booking_safe_success(self):
        """Test successful booking creation."""
        initial_slots = self.fitness_class.available_slots
        create_booking_safe(self.user, self.fitness_class)
        
        # Refresh from database
        self.fitness_class.refresh_from_db()
        
        # Check that booking was created
        self.assertEqual(Booking.objects.count(), 1)
        booking = Booking.objects.first()
        self.assertEqual(booking.client_email, self.user.email)
        self.assertEqual(booking.client_name, self.user.username)
        
        # Check that available slots decreased
        self.assertEqual(self.fitness_class.available_slots, initial_slots - 1)

    def test_create_booking_safe_no_slots(self):
        """Test booking creation fails when no slots available."""
        # Set available slots to 0
        self.fitness_class.available_slots = 0
        self.fitness_class.save()
        
        with self.assertRaises(ValueError) as context:
            create_booking_safe(self.user, self.fitness_class)
        
        self.assertIn("No slots available", str(context.exception))
        self.assertEqual(Booking.objects.count(), 0)

    def test_create_booking_safe_past_class(self):
        """Test booking creation fails for past classes."""
        # Set class time in the past
        self.fitness_class.datetime = timezone.now() - timedelta(hours=1)
        self.fitness_class.save()
        
        with self.assertRaises(ValueError) as context:
            create_booking_safe(self.user, self.fitness_class)
        
        self.assertIn("already started", str(context.exception))
        self.assertEqual(Booking.objects.count(), 0)

    def test_cancel_user_booking(self):
        """Test canceling a booking."""
        # Create a booking first
        booking = Booking.objects.create(
            client_name=self.user.username,
            client_email=self.user.email,
            fitness_class=self.fitness_class
        )
        self.fitness_class.available_slots -= 1
        self.fitness_class.save()
        
        initial_slots = self.fitness_class.available_slots
        
        # Cancel the booking
        cancel_user_booking(booking)
        
        # Refresh from database
        self.fitness_class.refresh_from_db()
        
        # Check that booking was deleted
        self.assertEqual(Booking.objects.count(), 0)
        
        # Check that available slots increased
        self.assertEqual(self.fitness_class.available_slots, initial_slots + 1)


class ViewsTest(TestCase):
    """Test cases for views."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            email='test@example.com'
        )
        self.admin = User.objects.create_user(
            username='admin',
            password='adminpass',
            email='admin@example.com',
            is_staff=True
        )
        self.fitness_class = FitnessClass.objects.create(
            name='Yoga',
            instructor='Alice',
            datetime=timezone.now() + timedelta(days=1),
            total_slots=10,
            available_slots=10
        )

    def test_home_view_anonymous(self):
        """Test home view for anonymous users."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        # Just check that the page loads successfully - adjust based on your actual template content
        self.assertContains(response, 'html')  # This should be present in any HTML page

    def test_home_view_authenticated_user(self):
        """Test home view redirects authenticated regular users."""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get('/')
        self.assertRedirects(response, reverse('user_dashboard'))

    def test_home_view_authenticated_admin(self):
        """Test home view redirects authenticated admin users."""
        self.client.login(username='admin', password='adminpass')
        response = self.client.get('/')
        self.assertRedirects(response, reverse('admin_dashboard'))

    def test_user_dashboard_access(self):
        """Test user dashboard access."""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('user_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Yoga')  # Should show available classes

    def test_admin_dashboard_access(self):
        """Test admin dashboard access."""
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_admin_dashboard_restricted_to_staff(self):
        """Test admin dashboard is restricted to staff users."""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('admin_dashboard'))
        # Should redirect to login or return 403
        self.assertNotEqual(response.status_code, 200)

    def test_book_class_success(self):
        """Test successful class booking."""
        self.client.login(username='testuser', password='testpass')
        initial_slots = self.fitness_class.available_slots
        
        response = self.client.post(
            reverse('book_class_page', kwargs={'class_id': self.fitness_class.id})
        )
        
        # Should redirect after successful booking
        self.assertEqual(response.status_code, 302)
        
        # Check booking was created
        self.assertEqual(Booking.objects.count(), 1)
        booking = Booking.objects.first()
        self.assertEqual(booking.client_email, self.user.email)
        
        # Check slots decreased
        self.fitness_class.refresh_from_db()
        self.assertEqual(self.fitness_class.available_slots, initial_slots - 1)

    def test_duplicate_booking_prevented(self):
        """Test that users cannot book the same class twice."""
        self.client.login(username='testuser', password='testpass')
        
        # Create initial booking
        Booking.objects.create(
            client_name=self.user.username,
            client_email=self.user.email,
            fitness_class=self.fitness_class
        )
        
        # Try to book again
        response = self.client.post(
            reverse('book_class_page', kwargs={'class_id': self.fitness_class.id})
        )
        
        # Should redirect (already booked)
        self.assertEqual(response.status_code, 302)
        
        # Should still have only one booking
        self.assertEqual(Booking.objects.count(), 1)


class APITest(TestCase):
    """Test cases for API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            email='test@example.com'
        )
        self.fitness_class = FitnessClass.objects.create(
            name='HIIT',
            instructor='Charlie',
            datetime=timezone.now() + timedelta(days=1),
            total_slots=8,
            available_slots=8
        )

    def test_api_requires_authentication(self):
        """Test that API endpoints require authentication."""
        response = self.client.get('/api/classes/')
        # DRF returns 403 for unauthenticated users when permission_classes = [IsAuthenticated]
        self.assertIn(response.status_code, [401, 403])  # Both are acceptable for auth required

    def test_api_classes_list(self):
        """Test API classes list endpoint."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/classes/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'HIIT')

    def test_api_create_booking(self):
        """Test API booking creation."""
        self.client.force_authenticate(user=self.user)
        data = {
            'class_id': self.fitness_class.id,
            'client_name': 'Test User'
        }
        response = self.client.post('/api/book/', data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Booking.objects.count(), 1)

    def test_api_my_bookings(self):
        """Test API my bookings endpoint."""
        # Create a booking
        Booking.objects.create(
            client_name=self.user.username,
            client_email=self.user.email,
            fitness_class=self.fitness_class
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/my-bookings/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['client_email'], self.user.email)


class ConcurrencyTest(TestCase):
    """Test cases for concurrency scenarios."""

    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            username='user1',
            password='pass1',
            email='user1@example.com'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='pass2',
            email='user2@example.com'
        )
        self.fitness_class = FitnessClass.objects.create(
            name='Yoga',
            instructor='Alice',
            datetime=timezone.now() + timedelta(days=1),
            total_slots=1,  # Only 1 slot to test race condition
            available_slots=1
        )

    def test_concurrent_booking_prevention(self):
        """Test that concurrent bookings are handled correctly."""
        # This is a simplified test - in reality, you'd need threading to test true concurrency
        # First booking should succeed
        create_booking_safe(self.user1, self.fitness_class)
        
        # Second booking should fail
        with self.assertRaises(ValueError):
            create_booking_safe(self.user2, self.fitness_class)
        
        # Should have only one booking
        self.assertEqual(Booking.objects.count(), 1)
        
        # Available slots should be 0
        self.fitness_class.refresh_from_db()
        self.assertEqual(self.fitness_class.available_slots, 0)