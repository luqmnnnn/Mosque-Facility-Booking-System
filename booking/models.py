from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta

# -------------------------
# 1. User Profile (USER Table)
# -------------------------
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)
    ic_number = models.CharField(max_length=20)
    role = models.CharField(max_length=10, choices=[('Admin', 'Admin'), ('Public', 'Public')])

# -------------------------
# 2. Facility (FACILITY Table)
# -------------------------
class Facility(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    rate = models.DecimalField(  # per 2-hour session
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Rate per session (2 hours)"
    )
    full_day_rate = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0.00,
        help_text="Flat rate for full-day bookings (08:00-22:00)"
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

# -------------------------
# 3. Booking (BOOKING Table)
# -------------------------
def generate_time_slots(start_hour=8, end_hour=22, slot_minutes=120):
    today = timezone.now().date()
    current = datetime.combine(today, datetime.min.time()) + timedelta(hours=start_hour)
    current = timezone.make_aware(current)
    end = datetime.combine(today, datetime.min.time()) + timedelta(hours=end_hour)
    end = timezone.make_aware(end)

    slots = [('08:00-22:00', 'Full Day')]
    while current + timedelta(minutes=slot_minutes) <= end:
        next_time = current + timedelta(minutes=slot_minutes)
        slot_key = f"{current.strftime('%H:%M')}-{next_time.strftime('%H:%M')}"
        slot_label = f"{current.strftime('%I:%M %p')} - {next_time.strftime('%I:%M %p')}"
        slots.append((slot_key, slot_label))
        current = next_time
    return slots

TIME_SLOTS = generate_time_slots()

class Booking(models.Model):
    EVENT_CHOICES = [
        ('Nikah', 'Nikah Ceremony'),
        ('Religious Class', 'Religious Class'),
        ('Community Event', 'Community Event'),
        ('Seminar', 'Seminar / Talk'),
        ('Workshop', 'Workshop / Training'),
        ('Other', 'Other Event'),
    ]


    STATUS_CHOICES = [
        ('Pending', 'Pending Approval'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='bookings', limit_choices_to={'is_active': True})
    event_type = models.CharField(max_length=30, choices=EVENT_CHOICES, default='Religious Class')
    event_date = models.DateField()
    time_slot = models.CharField(max_length=20, choices=TIME_SLOTS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    attendees = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.facility} - {self.event_date} ({self.get_time_slot_display()})"

    class Meta:
        ordering = ['-event_date', 'facility']
        permissions = [
            ("can_approve_booking", "Can approve or reject bookings"),
            ("can_view_all_bookings", "Can see all bookings (not just own)"),
        ]

    def clean(self):
        if self.event_date < timezone.now().date():
            raise ValidationError({'event_date': "Cannot book a date in the past."})

        approved_qs = Booking.objects.filter(
            facility=self.facility,
            event_date=self.event_date,
            status='Approved'
        ).exclude(pk=self.pk)

        if self.time_slot == '08:00-22:00':
            if approved_qs.exists():
                raise ValidationError({'time_slot': "Cannot book Full Day: there are approved bookings for this date."})
        else:
            if approved_qs.filter(time_slot='08:00-22:00').exists():
                raise ValidationError({'time_slot': "Cannot book this time: Full Day booking is already approved."})
            if approved_qs.filter(time_slot=self.time_slot).exists():
                raise ValidationError({'time_slot': "This time slot is already approved for the selected facility."})

# -------------------------
# 4. Payment (PAYMENT Table)
# -------------------------
from django.db.models.signals import pre_save
from django.dispatch import receiver

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('Cash', 'Cash'),
        ('Online Transfer', 'Online Transfer'),
        ('eWallet', 'eWallet'),
    ]

    booking = models.OneToOneField('Booking', on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_date = models.DateField(auto_now_add=True)
    receipt_file = models.FileField(upload_to='receipts/', null=True, blank=True)
    receipt_number = models.CharField(max_length=20, unique=True, blank=True)

    def __str__(self):
        return f"Payment for {self.booking} - {self.amount} via {self.method}"

@receiver(pre_save, sender=Payment)
def set_receipt_number(sender, instance, **kwargs):
    if not instance.receipt_number:
        last_payment = Payment.objects.all().order_by('id').last()
        last_id = last_payment.id if last_payment else 0
        instance.receipt_number = f"REC-{last_id + 1:04d}"
