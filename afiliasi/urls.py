from django.urls import path
from . import views

app_name = 'afiliasi'

urlpatterns = [
    path('',          views.info_recruiter,    name='info'),
    path('daftar/',   views.daftar_recruiter,  name='daftar'),
    path('dashboard/',views.dashboard_recruiter,name='dashboard'),
    path('cairkan/',  views.request_pencairan, name='cairkan'),
]