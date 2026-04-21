from django.db import migrations


def seed_templates(apps, schema_editor):
    TemplateFlyer = apps.get_model('afiliasi', 'TemplateFlyer')

    templates = [
        {
            'kode': 'story',
            'nama': 'Story / Reels',
            'deskripsi': 'Untuk Instagram Story, WhatsApp Status, TikTok, Facebook Story',
            'width': 1080,
            'height': 1920,
            'urutan': 1,
            'is_aktif': True,
        },
        {
            'kode': 'feed',
            'nama': 'Feed Post',
            'deskripsi': 'Untuk post Instagram Feed, Facebook, Twitter',
            'width': 1080,
            'height': 1080,
            'urutan': 2,
            'is_aktif': True,
        },
        {
            'kode': 'cetak',
            'nama': 'Flyer Cetak',
            'deskripsi': 'Untuk print A5/A4 dan share PDF via WhatsApp',
            'width': 1200,
            'height': 1800,
            'urutan': 3,
            'is_aktif': True,
        },
        {
            'kode': 'banner',
            'nama': 'Banner Landscape',
            'deskripsi': 'Untuk WhatsApp Group, Telegram, Facebook Cover',
            'width': 1920,
            'height': 1080,
            'urutan': 4,
            'is_aktif': True,
        },
    ]

    for data in templates:
        TemplateFlyer.objects.update_or_create(
            kode=data['kode'],
            defaults=data
        )


def reverse_seed(apps, schema_editor):
    TemplateFlyer = apps.get_model('afiliasi', 'TemplateFlyer')
    TemplateFlyer.objects.filter(
        kode__in=['story', 'feed', 'cetak', 'banner']
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('afiliasi', '0004_kontenflyer_templateflyer'),
    ]

    operations = [
        migrations.RunPython(seed_templates, reverse_seed),
    ]