from flask import Flask, render_template, request
import requests
import os  

app = Flask(__name__)

KATA_KBBI = set()
RANKING_KATA = {}

# --- OPTIMASI: SISTEM CACHE OFFLINE (Biar gak download terus) ---
URL_KBBI = "https://raw.githubusercontent.com/damzaky/kumpulan-kata-bahasa-indonesia-KBBI/refs/heads/master/list_1.0.0.txt"
URL_FREQ = "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2016/id/id_50k.txt"

print("\n==============================================")
print("⏳ [1/2] Mengecek data Kamus KBBI lokal...")
if not os.path.exists("kbbi_lokal.txt"):
    print("   🌐 File gak ada! Mendownload dari GitHub (cuma 1x doang)...")
    try:
        resp1 = requests.get(URL_KBBI, timeout=10)
        if resp1.status_code == 200:
            with open("kbbi_lokal.txt", "w", encoding="utf-8") as f:
                f.write(resp1.text)
            KATA_KBBI = set(k.strip().lower() for k in resp1.text.splitlines() if k.strip().isalpha())
            print(f"   ✅ Berhasil download & simpan {len(KATA_KBBI)} kata KBBI.")
    except Exception as e:
        print(f"   ⚠️ Gagal download KBBI: {e}")
else:
    print("   ⚡ Membaca KBBI dari penyimpanan lokal (Instan Wuzz!)...")
    try:
        with open("kbbi_lokal.txt", "r", encoding="utf-8") as f:
            KATA_KBBI = set(k.strip().lower() for k in f.read().splitlines() if k.strip().isalpha())
        print(f"   ✅ Berhasil load {len(KATA_KBBI)} kata KBBI dari cache.")
    except Exception as e:
        print(f"   ⚠️ Gagal baca file KBBI lokal: {e}")

print("\n⏳ [2/2] Mengecek data Ranking Kata lokal...")
if not os.path.exists("freq_lokal.txt"):
    print("   🌐 File gak ada! Mendownload dari GitHub (cuma 1x doang)...")
    try:
        resp2 = requests.get(URL_FREQ, timeout=10)
        if resp2.status_code == 200:
            with open("freq_lokal.txt", "w", encoding="utf-8") as f:
                f.write(resp2.text)
            for urutan, baris in enumerate(resp2.text.splitlines()):
                parts = baris.split()
                if parts:
                    kata = parts[0].strip().lower()
                    RANKING_KATA[kata] = urutan
            print(f"   ✅ Berhasil download & simpan ranking {len(RANKING_KATA)} kata.")
    except Exception as e:
        print(f"   ⚠️ Gagal download data frekuensi: {e}")
else:
    print("   ⚡ Membaca data Ranking dari penyimpanan lokal (Instan Wuzz!)...")
    try:
        with open("freq_lokal.txt", "r", encoding="utf-8") as f:
            for urutan, baris in enumerate(f.read().splitlines()):
                parts = baris.split()
                if parts:
                    kata = parts[0].strip().lower()
                    RANKING_KATA[kata] = urutan
        print(f"   ✅ Berhasil load ranking {len(RANKING_KATA)} kata dari cache.")
    except Exception as e:
        print(f"   ⚠️ Gagal baca file frekuensi lokal: {e}")
print("==============================================\n")
# --------------------------------------------------------

@app.route('/', methods=['GET', 'POST'])
def index():
    hasil_umum =[]
    pesan = ""
    awalan_input = ""

    if request.method == 'POST':
        awalan_input = request.form.get('awalan', '').lower().strip()
        
        if awalan_input and KATA_KBBI:
            # 1. Cari semua kata yang awalnya cocok dan panjang >= 3
            kata_valid =[k for k in KATA_KBBI if k.startswith(awalan_input) and len(k) >= 3]
            
            # 2. URUTAN SAKTI (Berdasarkan Frekuensi Penggunaan)
            hasil_umum = sorted(kata_valid, key=lambda k: (RANKING_KATA.get(k, 999999), k))
            
            # 3. FITUR ANTI NGE-LAG (Ambil Max 200 Teratas Aja)
            total_kata_ditemukan = len(hasil_umum)
            hasil_umum = hasil_umum[:200] 
            
            if total_kata_ditemukan > 0:
                if total_kata_ditemukan > 200:
                    pesan = f"✅ BERES! Total nemu {total_kata_ditemukan} kata (Menampilkan 200 kata paling populer aja bro):"
                else:
                    pesan = f"✅ BERES! Nemu {total_kata_ditemukan} kata:"
            else:
                pesan = f"❌ Gak nemu kata berawalan '{awalan_input}', bro."
        elif not KATA_KBBI:
             pesan = "⚠️ Kamus gagal dimuat, coba restart server."

    return render_template('index.html', hasil=hasil_umum, pesan=pesan, awalan=awalan_input)

if __name__ == '__main__':
    app.run(debug=True)