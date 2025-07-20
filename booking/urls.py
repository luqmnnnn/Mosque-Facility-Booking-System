from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'booking'

urlpatterns = [
    path('mosque_booking_system/home/', views.home, name='home'),
    path('mosque_booking_system/register/', views.register, name='register'),
    path('mosque_booking_system/login/', views.custom_login, name='login'),
    path('mosque_booking_system/logout/', auth_views.LogoutView.as_view(next_page='booking:login'), name='logout'),

    # Booking
    path('mosque_booking_system/booking/', views.make_booking, name='make_booking'),
    path('mosque_booking_system/my-bookings/', views.my_bookings, name='my_bookings'),
    path('mosque_booking_system/facilities/', views.facilities, name='facilities'),
    path('mosque_booking_system/admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('mosque_booking_system/edit-booking/<int:booking_id>/', views.edit_booking, name='edit_booking'),

    # Profile & Payment
    path('mosque_booking_system/profile/', views.profile_view, name='profile'),
    path('mosque_booking_system/payment/<int:booking_id>/', views.payment_page, name='payment_page'),
    path('mosque_booking_system/booking-slip/<int:booking_id>/', views.booking_slip, name='booking_slip'),
    path('mosque_booking_system/upload-receipt/<int:booking_id>/', views.upload_receipt, name='upload_receipt'),

    # Reports 
    path('mosque_booking_system/admin-reports/', views.booking_reports, name='booking_reports'),

    # Password Management
    path('mosque_booking_system/password-change/', auth_views.PasswordChangeView.as_view(
        template_name='registration/password_change_form.html'
    ), name='password_change'),
    path('mosque_booking_system/password-change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='registration/password_change_done.html'
    ), name='password_change_done'),
]
