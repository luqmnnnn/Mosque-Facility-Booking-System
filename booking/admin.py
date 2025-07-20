from django.contrib import admin
from .models import Facility, Booking, Payment, UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'ic_number', 'role')  
    search_fields = ('user__username', 'phone', 'ic_number')
    list_filter = ('role',)
    ordering = ('user__username',)

admin.site.register(Facility)
admin.site.register(Booking)
admin.site.register(Payment)
