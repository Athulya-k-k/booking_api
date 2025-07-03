# views.py
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from .forms import SignUpForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.contrib.auth.models import User
from django.db import transaction
import logging

from .models import FitnessClass, Booking
from .utils import (
    parse_datetime_from_form,
    is_valid_future_datetime,
    create_booking_safe,
    cancel_user_booking
)

logger = logging.getLogger(__name__)


def get_dashboard_redirect(user):
    """Redirect users to their respective dashboards."""
    return 'admin_dashboard' if user.is_staff else 'user_dashboard'

@never_cache
def signup_view(request):
    """Render the signup form and handle new user registration."""
    if request.user.is_authenticated:
        return redirect(get_dashboard_redirect(request.user))

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            logger.info(f"New user signed up: {user.username}")
            return redirect(get_dashboard_redirect(user))
        else:
            logger.warning(f"Signup form errors: {form.errors}")
    else:
        form = SignUpForm()

    return render(request, 'auth/signup.html', {'form': form})

@never_cache
def login_view(request):
    """Render login form and authenticate user."""
    if request.user.is_authenticated:
        return redirect(get_dashboard_redirect(request.user))

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        next_url = request.GET.get('next')
        logger.info(f"User logged in: {user.username}")
        return redirect(next_url or get_dashboard_redirect(user))

    return render(request, 'auth/login.html', {'form': form})

@never_cache
def logout_view(request):
    """Logout user."""
    logger.info(f"User logged out: {request.user.username}")
    logout(request)
    return redirect('home')  

@login_required
@user_passes_test(lambda u: u.is_staff)
@never_cache
def admin_dashboard(request):
    """Admin dashboard with list of classes and users."""
    classes = FitnessClass.objects.all().order_by('-datetime')
    bookings = Booking.objects.all()
    users = User.objects.filter(is_staff=False).order_by('username')
    return render(request, 'dashboard/admin_dashboard.html', {
        'classes': classes,
        'bookings': bookings,
        'users': users,
    })

@login_required
@user_passes_test(lambda u: not u.is_staff)
@never_cache
def user_dashboard(request):
    """User dashboard with list of available upcoming classes."""
    classes = FitnessClass.objects.filter(datetime__gte=timezone.now())
    user_bookings = Booking.objects.filter(client_email=request.user.email)
    booked_ids = user_bookings.values_list('fitness_class_id', flat=True)
    return render(request, 'dashboard/user_dashboard.html', {
        'classes': classes,
        'booked_ids': booked_ids,
        'user_bookings': user_bookings,
    })

@login_required
def book_class_page(request, class_id):
    """Allow user to book a class."""
    fitness_class = get_object_or_404(FitnessClass, id=class_id)
    already_booked = Booking.objects.filter(
        client_email=request.user.email,
        fitness_class=fitness_class
    ).exists()

    if already_booked:
        return redirect(get_dashboard_redirect(request.user))

    if request.method == 'POST':
        try:
            create_booking_safe(request.user, fitness_class)
            logger.info(f"{request.user.username} booked class: {fitness_class.name}")
            return redirect(get_dashboard_redirect(request.user))
        except ValueError as e:
            return render(request, 'book.html', {'cls': fitness_class, 'error': str(e)})

    return render(request, 'book.html', {'cls': fitness_class})

@login_required
def cancel_booking(request, booking_id):
    """Allow user to cancel their booking."""
    booking = get_object_or_404(Booking, id=booking_id, client_email=request.user.email)
    if request.method == 'POST':
        cancel_user_booking(booking)
        logger.info(f"{request.user.username} canceled booking: {booking.fitness_class.name}")
    return redirect(get_dashboard_redirect(request.user))

@never_cache
@user_passes_test(lambda u: u.is_staff)
def create_class(request):
    """Allow admin to create a new class."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        instructor = request.POST.get('instructor', '').strip()
        date = request.POST.get('date')
        time = request.POST.get('time')
        total_slots = request.POST.get('total_slots')
        error = None

        if not name or not instructor or not date or not time or not total_slots:
            error = "All fields are required."
        else:
            try:
                total = int(total_slots)
                if total <= 0:
                    error = "Total slots must be positive."
                class_datetime = parse_datetime_from_form(date, time)
                if not is_valid_future_datetime(class_datetime):
                    error = "Class must be scheduled in the future."
            except ValueError:
                error = "Invalid input for date, time, or slots."

        if error:
            return render(request, 'admin/create_class.html', {'error': error})

        FitnessClass.objects.create(
            name=name,
            instructor=instructor,
            datetime=class_datetime,
            total_slots=total,
            available_slots=total
        )
        logger.info(f"Class created: {name} by {instructor}")
        return redirect('admin_dashboard')

    return render(request, 'admin/create_class.html')

@never_cache
@user_passes_test(lambda u: u.is_staff)
def edit_class(request, class_id):
    """Allow admin to edit an existing class."""
    cls = get_object_or_404(FitnessClass, id=class_id)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        instructor = request.POST.get('instructor', '').strip()
        date = request.POST.get('date')
        time = request.POST.get('time')
        total_slots = request.POST.get('total_slots')
        available_slots = request.POST.get('available_slots')

        try:
            cls.name = name
            cls.instructor = instructor
            cls.datetime = parse_datetime_from_form(date, time)
            cls.total_slots = int(total_slots)
            cls.available_slots = int(available_slots)
            cls.save()
            logger.info(f"Class updated: {cls.name}")
            return redirect('admin_dashboard')
        except ValueError:
            return render(request, 'admin/edit_class.html', {
                'cls': cls,
                'error': 'Invalid input. Please check your entries.'
            })

    return render(request, 'admin/edit_class.html', {'cls': cls})

@user_passes_test(lambda u: u.is_staff)
def delete_class(request, class_id):
    """Allow admin to delete a class."""
    cls = get_object_or_404(FitnessClass, id=class_id)
    logger.warning(f"Class deleted: {cls.name}")
    cls.delete()
    return redirect('admin_dashboard')




def home_view(request):
    """Public homepage (index.html) view."""
    if request.user.is_authenticated:
        return redirect('admin_dashboard' if request.user.is_staff else 'user_dashboard')
    return render(request, 'index.html')