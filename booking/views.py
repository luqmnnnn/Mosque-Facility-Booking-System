from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from .models import Facility, Booking, UserProfile, Payment
from .forms import RegisterForm, BookingForm, FullProfileForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.admin.views.decorators import staff_member_required
from datetime import datetime, timedelta
from django.db.models import Count

# -----------------------------
# Home View
# -----------------------------
def home(request):
    return render(request, 'booking/home.html')


# -----------------------------
# Registration View
# -----------------------------
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully.')
            return redirect('booking:login')
    else:
        form = RegisterForm()
    return render(request, 'booking/register.html', {'form': form})
# -----------------------------
# Login View (Manual)
# -----------------------------
def custom_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, 'Logged in successfully.')
            return redirect('booking:home')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'booking/login.html')


# -----------------------------
# Make Booking View
# -----------------------------
@login_required
def make_booking(request):
    from .models import Facility  # optional, already imported above

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.status = 'Pending'
            booking.save()

            send_mail(
                subject='Booking Request Received',
                message=f'Your booking for {booking.facility.name} on {booking.event_date} at {booking.time_slot} has been submitted.',
                from_email=None,
                recipient_list=[request.user.email],
                fail_silently=True,
            )

            messages.success(request, 'Booking request submitted.')
            return redirect('booking:payment_page', booking.id)
    else:
        form = BookingForm()

    facilities = Facility.objects.filter(is_active=True)

    return render(request, 'booking/booking_form.html', {
        'form': form,
        'facilities': facilities
    })


# -----------------------------
# My Bookings View
# -----------------------------
@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user)

    if request.method == 'POST':
        booking_id = request.POST.get('booking_id')
        method = request.POST.get('method')
        receipt_file = request.FILES.get('receipt_file')

        booking = get_object_or_404(Booking, id=booking_id, user=request.user)

        # Case 1: Payment exists but no receipt uploaded yet
        if hasattr(booking, 'payment'):
            if not booking.payment.receipt_file:
                payment = booking.payment
                payment.method = method
                payment.receipt_file = receipt_file
                payment.save()
                messages.success(request, "Payment receipt uploaded successfully.")
            else:
                messages.error(request, "Receipt already uploaded. You cannot upload again.")
        
        # Case 2: No payment yet
        else:
            Payment.objects.create(
                booking=booking,
                amount=booking.facility.rate,
                method=method,
                receipt_file=receipt_file
            )
            messages.success(request, "Payment receipt uploaded successfully.")

        return redirect('booking:my_bookings')

    return render(request, 'booking/my_bookings.html', {'bookings': bookings})

# -----------------------------
# Admin Dashboard View
# -----------------------------
@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('booking:home')

    if request.method == 'POST':
        booking_id = request.POST.get('booking_id')
        action = request.POST.get('action')
        booking = get_object_or_404(Booking, id=booking_id)

        if action == 'approve':
            booking.status = 'Approved'
            status_msg = 'approved'
        elif action == 'reject':
            booking.status = 'Rejected'
            status_msg = 'rejected'
        elif action == 'delete':
            booking.delete()
            messages.success(request, 'Booking deleted successfully.')
            return redirect('booking:admin_dashboard')

        if action in ['approve', 'reject']:
            booking.save()
            send_mail(
                subject=f'Your Booking has been {status_msg}',
                message=f'Your booking for {booking.facility.name} on {booking.event_date} at {booking.time_slot} has been {status_msg}.',
                from_email=None,
                recipient_list=[booking.user.email],
                fail_silently=True,
            )
            messages.success(request, f'Booking has been {status_msg}.')

    bookings = Booking.objects.all()
    return render(request, 'booking/admin_dashboard.html', {'bookings': bookings})


# -----------------------------
# Edit Booking (Admin Only)
# -----------------------------
@login_required
def edit_booking(request, booking_id):
    if not request.user.is_staff:
        return redirect('booking:home')

    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            messages.success(request, 'Booking updated successfully.')
            return redirect('booking:admin_dashboard')
    else:
        form = BookingForm(instance=booking)

    return render(request, 'booking/edit_booking.html', {'form': form, 'booking': booking})


# -----------------------------
# View Available Facilities
# -----------------------------
def facilities(request):
    selected_date = request.GET.get('date')
    try:
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        selected_date = datetime.now().date()

    facilities_list = Facility.objects.filter(is_active=True)

    facility_availability = []
    for facility in facilities_list:
        bookings_on_date = Booking.objects.filter(facility=facility, event_date=selected_date)
        facility_availability.append({
            'facility': facility,
            'booked': bookings_on_date.exists(),
            'bookings': bookings_on_date
        })

    return render(request, 'booking/facilities.html', {
        'facility_availability': facility_availability,
        'selected_date': selected_date
    })


# -----------------------------
# Payment Page
# -----------------------------
import uuid 

def payment_page(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    # Determine correct amount
    if booking.time_slot == "08:00-22:00" and booking.facility.full_day_rate:
        payment_amount = booking.facility.full_day_rate
    else:
        payment_amount = booking.facility.rate

    if request.method == 'POST':
        method = request.POST.get('method')
        receipt_file = request.FILES.get('receipt_file')

        payment, created = Payment.objects.get_or_create(
            booking=booking,
            defaults={
                'amount': payment_amount
            }
        )

        payment.method = method
        if receipt_file:
            payment.receipt_file = receipt_file
            messages.success(request, "✅ Payment receipt uploaded successfully.")
        else:
            messages.info(request, "ℹ️ You can upload the receipt later in 'My Bookings'.")

        payment.save()
        return redirect('booking:payment_page', booking_id=booking.id)

    return render(request, 'booking/payment_page.html', {
        'booking': booking,
        'amount': payment_amount  # Pass this to template
    })

# -----------------------------
# Payment Success
# -----------------------------
@login_required
def booking_slip(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if not hasattr(booking, 'payment'):
        messages.error(request, "No payment found for this booking.")
        return redirect('booking:my_bookings')

    return render(request, 'booking/booking_slip.html', {'payment': booking.payment})


@login_required
def profile_view(request):
    user = request.user
    profile = UserProfile.objects.get(user=user)

    if request.method == 'POST':
        form = FullProfileForm(request.POST, instance=profile)

        user.email = request.POST.get('email')
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')

        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password:
            if new_password == confirm_password:
                user.set_password(new_password)
                update_session_auth_hash(request, user)  # ✅ Keeps user logged in
                messages.success(request, 'Password updated successfully.')
            else:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'booking/profile.html', {
                    'form': form,
                    'user': user
                })

        user.save()

        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('booking:profile')
    else:
        form = FullProfileForm(instance=profile)

    return render(request, 'booking/profile.html', {
        'form': form,
        'user': user
    })

from django.views.decorators.http import require_POST

@login_required
@require_POST
def upload_receipt(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    receipt = request.FILES.get('receipt_file')

    if not receipt:
        messages.error(request, "Please upload a receipt.")
        return redirect('booking:my_bookings')

    if hasattr(booking, 'payment'):
        # Update existing payment
        booking.payment.receipt_file = receipt
        booking.payment.save()
    else:
        # Create new payment
        Payment.objects.create(
            booking=booking,
            amount=booking.facility.rate,
            method='Manual Upload',\
            receipt_file=receipt
        )

    messages.success(request, "Receipt uploaded successfully.")
    return redirect('booking:my_bookings')

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
@staff_member_required
def booking_reports(request):
    from datetime import datetime, timedelta
    import calendar

    period = request.GET.get('period', 'daily')
    today = datetime.today().date()

    selected_date = today
    selected_week = ''
    selected_month = ''

    if period == 'daily':
        date_str = request.GET.get('date')
        if date_str:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_date = selected_date
        end_date = selected_date + timedelta(days=1)

    elif period == 'weekly':
        week_str = request.GET.get('week')
        if week_str:
            year, week = map(int, week_str.split('-W'))
            start_date = datetime.strptime(f'{year}-W{week}-1', "%Y-W%W-%w").date()
        else:
            start_date = today - timedelta(days=7)
        end_date = start_date + timedelta(days=7)
        selected_week = week_str or today.strftime('%Y-W%W')

    elif period == 'monthly':
        month_str = request.GET.get('month')
        if month_str:
            year, month = map(int, month_str.split('-'))
            start_date = datetime(year, month, 1).date()
        else:
            start_date = today.replace(day=1)
        last_day = calendar.monthrange(start_date.year, start_date.month)[1]
        end_date = start_date.replace(day=last_day) + timedelta(days=1)
        selected_month = month_str or today.strftime('%Y-%m')

    else:
        start_date = today
        end_date = today + timedelta(days=1)

    bookings = Booking.objects.filter(
        event_date__gte=start_date,
        event_date__lt=end_date
    ).order_by('-event_date')

    # ✅ Count only APPROVED bookings by facility
    facility_usage = (
        bookings.filter(status='Approved')
        .values('facility__name')
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    approved_count = bookings.filter(status='Approved').count()
    rejected_count = bookings.filter(status='Rejected').count()
    pending_count = bookings.filter(status='Pending').count()

    return render(request, 'booking/booking_reports.html', {
        'bookings': bookings,
        'facility_usage': facility_usage,
        'selected_period': period,
        'selected_date': selected_date,
        'selected_week': selected_week,
        'selected_month': selected_month,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'pending_count': pending_count,
    })

