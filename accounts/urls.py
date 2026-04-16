from django.urls import path
from . import views, api

app_name = 'accounts'

urlpatterns = [
    path('daftar/',                    views.registrasi,        name='registrasi'),
    path('daftar/sukses/',             views.registrasi_sukses, name='registrasi_sukses'),
    path('aktivasi/<uuid:token>/',     views.aktivasi,          name='aktivasi'),
    path('aktivasi/sukses/',           views.aktivasi_sukses,   name='aktivasi_sukses'),
    path('login/',                     views.login_view,        name='login'),
    path('logout/',                    views.logout_view,       name='logout'),

    # API dynamic dropdown
    path('api/kabupaten-kota/',        api.api_kabupaten_kota,  name='api_kabupaten_kota'),
    path('api/kecamatan/',             api.api_kecamatan,       name='api_kecamatan'),
    path('api/sekolah/',               api.api_sekolah,         name='api_sekolah'),
    path('pengumuman/<int:pk>/', views.pengumuman_detail, name='pengumuman_detail'),
]