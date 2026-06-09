from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', RedirectView.as_view(url='/static/index.html', permanent=False)),
    path('api/', include('api.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
