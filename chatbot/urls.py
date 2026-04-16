from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('kirim/',              views.kirim_pesan,   name='kirim'),
    path('riwayat/<session_id>/', views.riwayat_sesi, name='riwayat'),
]