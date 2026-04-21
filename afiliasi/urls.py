from django.urls import path
from . import views

app_name = 'afiliasi'

urlpatterns = [
    path('',          views.info_recruiter,    name='info'),
    path('daftar/',   views.daftar_recruiter,  name='daftar'),
    path('dashboard/',views.dashboard_recruiter,name='dashboard'),
    path('cairkan/',  views.request_pencairan, name='cairkan'),

    # ========== FLYER GENERATOR ==========
    path('flyer/preview/<str:kode_template>/',
         views.flyer_preview,
         name='flyer_preview'),
    path('flyer/download/png/<str:kode_template>/',
         views.flyer_download_png,
         name='flyer_download_png'),
    path('flyer/download/pdf/<str:kode_template>/',
         views.flyer_download_pdf,
         name='flyer_download_pdf'),
]