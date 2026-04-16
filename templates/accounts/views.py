def beranda(request):
    """Halaman beranda publik"""
    from konten.models import Pengumuman, Testimoni, MitraKerjasama, MediaSosial, DokumenDownload, BrosurFakultas
    from master.models import JalurPenerimaan, GelombangPenerimaan, PengaturanSistem
    from utils.simda_reader import get_fakultas, get_program_studi
    from django.utils import timezone

    pengaturan      = PengaturanSistem.get()
    jalur_list      = JalurPenerimaan.objects.filter(status='aktif').order_by('urutan')
    gelombang_aktif = GelombangPenerimaan.objects.filter(status='buka').select_related('jalur')
    pengumuman_penting = Pengumuman.objects.filter(
        status='aktif', penting=True,
        tgl_tayang__lte=timezone.now().date()
    ).order_by('-tgl_tayang')[:3]
    pengumuman_list = Pengumuman.objects.filter(
        status='aktif',
        tgl_tayang__lte=timezone.now().date()
    ).order_by('-penting', '-tgl_tayang')[:6]
    testimoni_list  = Testimoni.objects.filter(status='aktif').order_by('urutan')[:3]
    mitra_list      = MitraKerjasama.objects.filter(status='aktif').order_by('urutan')[:12]
    medsos_list     = MediaSosial.objects.filter(status='aktif').order_by('urutan')
    dokumen_list    = DokumenDownload.objects.filter(status='aktif').order_by('urutan')[:4]

    # Fakultas dari SIMDA + prodi + brosur
    try:
        fakultas_raw = get_fakultas()
        prodi_raw    = get_program_studi(jenjang='S1')
        brosur_map   = {b.kode_fakultas: b for b in BrosurFakultas.objects.filter(status='aktif')}

        fakultas_list = []
        for f in fakultas_raw:
            kode = f['kode_fakultas']
            prodi_list = [p for p in prodi_raw if p['kode_fakultas'] == kode]
            fakultas_list.append({
                'kode_fakultas': kode,
                'nama_fakultas': f['nama_fakultas'],
                'prodi_count':   len(prodi_list),
                'prodi_list':    prodi_list,
                'brosur':        brosur_map.get(kode),
            })
    except Exception:
        fakultas_list = []

    steps = [
        {'judul': 'Isi data awal',     'sub': 'Nama, email, jalur'},
        {'judul': 'Aktivasi email',     'sub': 'Klik link di email'},
        {'judul': 'Lengkapi profil',    'sub': 'Data diri & dokumen'},
        {'judul': 'Bayar pendaftaran',  'sub': 'Transfer atau QRIS'},
        {'judul': 'Ikuti seleksi',      'sub': 'Tes & pengumuman'},
    ]

    context = {
        'pengaturan':        pengaturan,
        'jalur_list':        jalur_list,
        'gelombang_aktif':   gelombang_aktif,
        'pengumuman_penting':pengumuman_penting,
        'pengumuman_list':   pengumuman_list,
        'testimoni_list':    testimoni_list,
        'mitra_list':        mitra_list,
        'medsos_list':       medsos_list,
        'dokumen_list':      dokumen_list,
        'fakultas_list':     fakultas_list,
        'steps':             steps,
        'total_jalur':       jalur_list.count(),
        'status_pmb':        'Buka' if pengaturan.status_pendaftaran == 'buka' else 'Tutup',
    }
    return render(request, 'publik/beranda.html', context)