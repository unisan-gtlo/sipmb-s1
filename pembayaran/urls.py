# pembayaran/urls.py
from django.urls import path
from . import views

app_name = 'pembayaran'


urlpatterns = [
    path('', views.daftar_tagihan, name='daftar'),
    path('return/duitku/', views.duitku_return, name='duitku_return'),           # BARU — harus di atas <kode_bayar> pattern
    path('callback/duitku/', views.duitku_callback, name='duitku_callback'), 
    path('<str:kode_bayar>/', views.detail_tagihan, name='detail'),
    path('<str:kode_bayar>/kwitansi/', views.kwitansi, name='kwitansi'),
    path('<str:kode_bayar>/duitku/', views.duitku_pilih_metode, name='duitku_pilih'),   # BARU
    path('<str:kode_bayar>/duitku/create/', views.duitku_create, name='duitku_create'), # BARU
    path('<str:kode_bayar>/batalkan/', views.batalkan_pembayaran, name='batalkan'),
]