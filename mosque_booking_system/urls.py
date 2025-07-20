from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/mosque_booking_system/login/', permanent=False)),
    path('', include('booking.urls', namespace='booking')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)