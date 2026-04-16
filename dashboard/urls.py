from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('',           views.index,              name='index'),
    path('maba/',      views.calon_maba,          name='calon_maba'),
    path('admin/',     views.admin_pmb,           name='admin'),
    path('recruiter/', views.recruiter_dashboard, name='recruiter'),
]