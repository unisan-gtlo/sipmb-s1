from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('daftar/',                    views.registrasi,       name='registrasi'),
    path('daftar/sukses/',             views.registrasi_sukses,name='registrasi_sukses'),
    path('aktivasi/<uuid:token>/',     views.aktivasi,         name='aktivasi'),
    path('aktivasi/sukses/',           views.aktivasi_sukses,  name='aktivasi_sukses'),
    path('login/',                     views.login_view,        name='login'),
    path('logout/',                    views.logout_view,       name='logout'),
]