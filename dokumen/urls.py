from django.urls import path
from . import views

app_name = 'dokumen'

urlpatterns = [
    path('',                        views.daftar_dokumen, name='daftar'),
    path('<int:dokumen_id>/upload/', views.upload_dokumen, name='upload'),
    path('<int:dokumen_id>/hapus/',  views.hapus_dokumen,  name='hapus'),
]