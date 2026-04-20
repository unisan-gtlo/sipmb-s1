# pembayaran/urls.py
from django.urls import path
from . import views

app_name = 'pembayaran'

urlpatterns = [
    path('', views.daftar_tagihan, name='daftar'),
    path('<str:kode_bayar>/', views.detail_tagihan, name='detail'),
    path('<str:kode_bayar>/kwitansi/', views.kwitansi, name='kwitansi'),
]