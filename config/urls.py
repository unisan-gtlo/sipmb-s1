from django.shortcuts import render

def ratelimited_view(request, exception=None):
    return render(request, '429.html', status=429)

handler429 = 'config.urls.ratelimited_view'

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import beranda

urlpatterns = [
    path('',          beranda,                                    name='beranda'),
    path('admin/',        admin.site.urls),
    path('accounts/',     include('accounts.urls',    namespace='accounts')),
    path('dashboard/',    include('dashboard.urls',   namespace='dashboard')),
    path('profil/',       include('pendaftaran.urls', namespace='pendaftaran')),
    path('dokumen/',      include('dokumen.urls',     namespace='dokumen')),
    path('sinta/',        include('chatbot.urls',     namespace='chatbot')),
    path('admin-pmb/',    include('admin_pmb.urls',   namespace='admin_pmb')),
    path('afiliasi/', include('afiliasi.urls',     namespace='afiliasi')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])