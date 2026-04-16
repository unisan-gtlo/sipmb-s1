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
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])