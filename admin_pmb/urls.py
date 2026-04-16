from django.urls import path
from . import views

app_name = 'admin_pmb'

urlpatterns = [
    path('',            views.dashboard,   name='dashboard'),
    path('pendaftar/',  views.pendaftar,   name='pendaftar'),
    path('pendaftar/<int:pk>/', views.detail_pendaftar, name='detail_pendaftar'),
    path('verifikasi/', views.verifikasi,  name='verifikasi'),
    path('verifikasi/<int:dok_id>/acc/',  views.verif_acc,   name='verif_acc'),
    path('verifikasi/<int:dok_id>/tolak/', views.verif_tolak, name='verif_tolak'),
    path('pembayaran/', views.pembayaran,  name='pembayaran'),
    path('seleksi/',    views.seleksi,     name='seleksi'),
    path('hasil/',      views.hasil,       name='hasil'),
    path('master/',     views.master,      name='master'),
    path('konten/',     views.konten,      name='konten'),
    path('afiliasi/',   views.afiliasi,    name='afiliasi'),
    path('laporan/',    views.laporan,     name='laporan'),
    path('chatbot/',    views.chatbot_kb,  name='chatbot_kb'),
    path('pendaftar/<int:pk>/status/', views.ubah_status, name='ubah_status'),
]