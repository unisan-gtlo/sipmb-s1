"""Download logo metode pembayaran dari Duitku — URL asli dari project 29766."""
import os
import urllib.request
import time

TARGET_DIR = os.path.join('static', 'img', 'duitku')
os.makedirs(TARGET_DIR, exist_ok=True)

# URL asli dari sandbox.duitku.com/merchant/Content/Image/PG/
LOGOS = {
    'bca.png':         'https://sandbox.duitku.com/merchant/Content/Image/PG/BCA.SVG',
    'mandiri.png':     'https://sandbox.duitku.com/merchant/Content/Image/PG/MV.PNG',
    'bni.png':         'https://sandbox.duitku.com/merchant/Content/Image/PG/I1.PNG',
    'cimb.png':        'https://sandbox.duitku.com/merchant/Content/Image/PG/B1.PNG',
    'permata.png':     'https://sandbox.duitku.com/merchant/Content/Image/PG/PERMATA.PNG',
    'bsi.png':         'https://sandbox.duitku.com/merchant/Content/Image/PG/BSI.PNG',
    'bri.png':         'https://sandbox.duitku.com/merchant/Content/Image/PG/BR.PNG',
    'atm_bersama.png': 'https://sandbox.duitku.com/merchant/Content/Image/PG/A1.PNG',
    'shopeepay.png':   'https://sandbox.duitku.com/merchant/Content/Image/PG/SHOPEEPAY.PNG',
    'ovo.png':         'https://sandbox.duitku.com/merchant/Content/Image/PG/OV.PNG',
    'dana.png':        'https://sandbox.duitku.com/merchant/Content/Image/PG/DA.PNG',
    'linkaja.png':     'https://sandbox.duitku.com/merchant/Content/Image/PG/LINKAJA.PNG',
    'qris.png':        'https://sandbox.duitku.com/merchant/Content/Image/PG/NQ.PNG',
    'indomaret.png':   'https://sandbox.duitku.com/merchant/Content/Image/PG/IR.PNG',
    'alfamart.png':    'https://sandbox.duitku.com/merchant/Content/Image/PG/FT.PNG',
    'retail.png':      'https://sandbox.duitku.com/merchant/Content/Image/PG/RETAIL.PNG',
    'credit_card.png': 'https://sandbox.duitku.com/merchant/Content/Image/PG/VC.PNG',
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'image/*,*/*',
    'Referer': 'https://sandbox.duitku.com/',
}

print(f"Downloading {len(LOGOS)} logos...\n")

success, failed = 0, []
for filename, url in LOGOS.items():
    # Kalau URL .SVG, simpan .svg (bukan .png)
    if url.lower().endswith('.svg'):
        filename = filename.replace('.png', '.svg')
    target = os.path.join(TARGET_DIR, filename)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            data = response.read()
        with open(target, 'wb') as f:
            f.write(data)
        size_kb = len(data) / 1024
        print(f"  OK  {filename:<25} ({size_kb:.1f} KB)")
        success += 1
    except Exception as e:
        print(f"  --  {filename:<25} FAILED: {str(e)[:50]}")
        failed.append(filename)
    time.sleep(0.2)

print(f"\nDone: {success}/{len(LOGOS)} success")
if failed:
    print(f"Failed: {failed}")