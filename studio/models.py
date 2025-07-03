from django.db import models
from django.utils import timezone

class FitnessClass(models.Model):
    CLASS_TYPES = [
        ('Yoga', 'Yoga'),
        ('Zumba', 'Zumba'),
        ('HIIT', 'HIIT'),
    ]
    name = models.CharField(choices=CLASS_TYPES, max_length=10)
    instructor = models.CharField(max_length=100)
    datetime = models.DateTimeField()
    total_slots = models.PositiveIntegerField()
    available_slots = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.name} on {self.datetime}"

class Booking(models.Model):
    fitness_class = models.ForeignKey(
        FitnessClass,
        on_delete=models.CASCADE,
        related_name='bookings'  # ✅ This allows cls.bookings.all in template
    )
    client_name = models.CharField(max_length=100)
    client_email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client_name} - {self.fitness_class.name}"
