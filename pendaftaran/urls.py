from django.urls import path
from . import views

app_name = 'pendaftaran'

urlpatterns = [
    path('',             views.profil_diri,       name='profil_diri'),
    path('ortu/',        views.profil_ortu,        name='profil_ortu'),
    path('pendidikan/',  views.profil_pendidikan,  name='profil_pendidikan'),
    path('foto/',        views.profil_foto,        name='profil_foto'),
    path('kartu-peserta/', views.cetak_kartu_maba, name='cetak_kartu'),
    path('formulir/', views.cetak_formulir, name='cetak_formulir'),
]