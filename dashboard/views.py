from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


@login_required
def index(request):
    user = request.user

    # Arahkan ke dashboard sesuai role
    if user.role in ['admin_pmb', 'operator_pmb', 'panitia_seleksi', 'pimpinan']:
        return render(request, 'dashboard/admin.html', {'user': user})
    elif user.role == 'recruiter':
        return render(request, 'dashboard/recruiter.html', {'user': user})
    else:
        # calon_maba
        return render(request, 'dashboard/calon_maba.html', {'user': user})