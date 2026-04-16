from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ['username', 'nama_lengkap', 'email', 'role', 'is_sso_user', 'is_active']
    list_filter   = ['role', 'is_sso_user', 'is_active', 'is_staff']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering      = ['username']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Info SIPMB', {
            'fields': ('role', 'no_hp', 'jenis_kelamin', 'foto', 'is_sso_user', 'sso_uuid')
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Info SIPMB', {
            'fields': ('role', 'no_hp', 'jenis_kelamin', 'foto')
        }),
    )