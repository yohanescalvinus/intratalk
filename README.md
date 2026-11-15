# 🎙️ IntraTalk — Walkie-Talkie LAN Tanpa Internet

Aplikasi komunikasi suara (**Push-to-Talk**) berbasis web yang berjalan **sepenuhnya di jaringan lokal (LAN)** tanpa koneksi internet. Cukup jalankan server di laptop, scan QR Code dari HP, dan mulai berkomunikasi.

| Status | Platform | Python | Lisensi |
|---|---|---|---|
| ✅ Active | Windows 10/11 | 3.12 | MIT |

---

## ✨ Fitur

- 🎙️ **Push-to-Talk (PTT)** antar perangkat di channel yang sama
- 💬 **Chat teks** real-time per channel
- 🔔 **Buzzer / panggilan** ke channel atau pengguna tertentu
- 👥 **Multi-channel** (channel 1, 2, 3, ...)
- 🖥️ **Pusat Komando (Admin)** lewat CMD:
  - `/listen`, `/listenhistory`, `/pttlog`, `/users`, `/kick`, `/ring`, `/chat`
- 📱 **QR Code otomatis** untuk akses cepat dari HP
- 🔐 **HTTPS self-signed** (wajib untuk akses mikrofon di browser HP)
- 📲 **PWA-ready** — bisa di-*install* ke home screen HP seperti aplikasi native

---

## 📋 Prasyarat

- **Windows 10/11** (dengan `winget` tersedia)
- **Python 3.12**
- Folder aplikasi harus berisi **`index.html`** (frontend)
- HP dan laptop terhubung ke **jaringan Wi-Fi/LAN yang sama**

> ℹ️ **Tidak butuh Node.js, tidak butuh `npm`.** Aplikasi ini 100% berjalan di Python.

---

## 🚀 Instalasi

### 📦 1. Instal Python

Jika di laptop belum ada Python, buka **CMD** dan jalankan:

```cmd
winget install Python.Python.3.12
```

> ⚠️ **PENTING:** Setelah instalasi selesai, **TUTUP CMD** lalu **buka CMD baru**. Ini wajib agar Windows mengenali perintah `python`.

### 📚 2. Instal Library Python

Di CMD baru, masuk ke folder aplikasi:

```cmd
cd C:\intratalk
```

> _(Sesuaikan `C:\intratalk` dengan lokasi folder aplikasi Anda)._

Lalu instal dependensi:

```cmd
pip install aiohttp pyopenssl qrcode
```

**Penjelasan Library:**

| Library | Fungsi |
|---|---|
| `aiohttp` | Server web HTTPS + WebSocket antar HP |
| `pyopenssl` | Membuat sertifikat SSL otomatis (wajib untuk akses mikrofon) |
| `qrcode` | Menampilkan QR Code di layar CMD |

### ▶️ 3. Jalankan Server

```cmd
python server.py
```

Server akan menyala di port **8443**, QR Code muncul di CMD, dan Anda siap bertempur! 🎙️🖥️

---

## 📁 Struktur Folder

```
intratalk/
├── index.html            # Frontend walkie-talkie (PWA)
├── manifest.json         # Manifest PWA
├── service-worker.js     # Cache PWA
├── server.py             # ✅ Server utama (Python)
├── icons/                # Ikon PWA
│   ├── icon-192.png
│   └── icon-512.png
└── README.md             # Dokumentasi ini
```

### 📌 File yang Dibuat Otomatis

| File | Kapan dibuat |
|---|---|
| `cert.pem` | Saat `server.py` pertama kali dijalankan |
| `key.pem` | Saat `server.py` pertama kali dijalankan |
| `__pycache__/` | Saat Python menjalankan skrip |

> 📌 **Catatan:** `cert.pem` dan `key.pem` **tidak disertakan** dalam paket. Keduanya dibuat otomatis oleh `server.py` sesuai IP laptop masing-masing.

### 🗑️ File yang Tidak Diperlukan

File berikut **tidak dipakai** oleh `server.py` dan boleh dihapus atau diabaikan:

- `server.js` — server signaling PeerJS (alternatif, tidak dipakai)
- `package.json` — dependensi Node.js (tidak dipakai)
- `package-lock.json` — lockfile Node.js (tidak dipakai)
- `node_modules/` — folder dependensi Node.js (tidak dipakai)

---

## 🎯 Cara Menggunakan

1. Jalankan server:
   ```cmd
   python server.py
   ```
2. QR Code muncul di layar CMD.
3. Di HP, buka browser → izinkan akses kamera.
4. Scan QR Code di layar laptop.
5. Izinkan akses **mikrofon** saat browser meminta.
6. Isi **nama** dan **channel**, lalu masuk.
7. Ulangi untuk semua HP yang ingin terhubung.
8. Tekan & tahan tombol PTT untuk bicara. 🎙️

> 🌐 URL akses manual: `https://<IP-LAPTOP>:8443`

---

## 📲 Install sebagai Aplikasi (PWA)

IntraTalk sudah mendukung **PWA (Progressive Web App)** — artinya bisa di-*install* ke home screen HP dan berjalan seperti aplikasi native (fullscreen, tanpa address bar).

### Di Android (Chrome):

1. Buka `https://<IP-LAPTOP>:8443` di Chrome
2. Ketuk menu **⋮** (titik tiga) di kanan atas
3. Pilih **"Add to Home screen"** atau **"Install app"**
4. Ikon **IntraTalk** muncul di home screen
5. Buka dari ikon → tampil **fullscreen** seperti app biasa

### Di iOS (Safari):

1. Buka `https://<IP-LAPTOP>:8443` di Safari
2. Ketuk tombol **Share** (kotak dengan panah ke atas)
3. Pilih **"Add to Home Screen"**
4. Ikon **IntraTalk** muncul di home screen

> 💡 **Tips:** Setelah di-install, aplikasi bisa dibuka lebih cepat dan tampil lebih bersih tanpa UI browser.

---

## 🖥️ Perintah Pusat Komando (Admin)

Saat `server.py` berjalan, Anda bisa mengetik perintah di CMD:

| Perintah | Fungsi |
|---|---|
| `/help` | Lihat daftar perintah |
| `/qr` | Tampilkan ulang QR Code |
| `/clear` | Bersihkan layar CMD |
| `/exit` | Matikan server dengan rapi |
| `/users` | Lihat semua pengguna |
| `/users <channel>` | Lihat pengguna di channel tertentu |
| `/listen <channel>` | Pantau aktivitas 1 channel |
| `/listen <channel> <nama>` | Pantau 1 orang tertentu |
| `/listen all` | Pantau semua channel |
| `/listenhistory <channel>` | Riwayat chat 1 channel |
| `/listenhistory <channel> <nama>` | Riwayat chat 1 orang |
| `/listenhistory all` | Riwayat chat semua channel |
| `/pttlog <channel>` | Rekap aktivitas PTT per channel |
| `/pttlog <channel> <nama>` | Rekap PTT 1 orang |
| `/pttlog` atau `/pttlog all` | Rekap PTT semua channel |
| `/chat <channel> <pesan>` | Kirim chat ke 1 channel |
| `/chat <channel> <nama> <pesan>` | Kirim chat privat ke 1 orang |
| `/ring <channel>` | Alarm ke seluruh channel |
| `/ring <channel> <nama>` | Alarm ke 1 orang |
| `/ring` (tanpa argumen) | Alarm ke **SEMUA channel** sekaligus |
| `/kick <channel>` | Tendang semua orang di channel |
| `/kick <channel> <nama>` | Tendang 1 orang |

> 💡 **Broadcast pesan:** Ketik pesan **tanpa** awalan `/` untuk mengirim ke **semua channel**.

---

## 🌐 Detail Port & URL

| Item | Nilai |
|---|---|
| Port server | `8443` |
| Protokol | `HTTPS` (self-signed) |
| URL akses | `https://<IP-LAPTOP>:8443` |
| WebSocket endpoint | `wss://<IP-LAPTOP>:8443/ws` |

> ⚠️ `service-worker.js` **mengecualikan** request ke port `:8443` dari cache — ini penting agar koneksi signaling tidak terganggu.

---

## 🔐 Catatan Keamanan

- **Tidak ada autentikasi admin.** Siapa pun yang mengakses CMD laptop bisa menjalankan perintah admin.
- **Tidak ada password channel.** Siapa pun di jaringan yang sama bisa bergabung ke channel mana pun.
- **Data tidak persisten.** Chat & PTT history disimpan di memori (max 1000 entri) dan hilang saat server restart.
- **HTTPS self-signed.** Browser HP akan menampilkan peringatan sertifikat — ini **normal** untuk LAN. Klik "Advanced → Proceed" untuk lanjut.
- **Cocok untuk penggunaan internal terpercaya** (tim, keluarga, acara), **bukan** untuk jaringan publik.

---

## ❓ Troubleshooting

| Masalah | Solusi |
|---|---|
| `python` tidak dikenali | Tutup CMD, buka CMD baru (lihat langkah instalasi) |
| `pip` tidak dikenali | Cek: `python --version`, lalu `python -m pip install aiohttp pyopenssl qrcode` |
| `index.html` tidak ditemukan | Pastikan `index.html` ada di folder yang sama dengan `server.py` |
| `cert.pem` / `key.pem` tidak ada | **Normal.** Jalankan `python server.py`, file akan dibuat otomatis |
| Sertifikat tidak valid setelah pindah Wi-Fi | Hapus `cert.pem` dan `key.pem`, lalu jalankan ulang `python server.py` |
| HP tidak bisa akses | Pastikan HP & laptop di **Wi-Fi yang sama**, cek firewall |
| Mikrofon tidak jalan | Wajib HTTPS. Terima peringatan sertifikat di browser HP |
| Port 8443 dipakai | Ganti `PORT = 8443` di `server.py` ke angka lain (mis. 8444) |
| Firewall blokir | Izinkan `python.exe` di Windows Defender Firewall (Private network) |
| History chat/PTT hilang setelah restart | **Normal** — data disimpan di memori, tidak persisten |
| PWA tidak muncul "Install app" | Pastikan akses via HTTPS dan `manifest.json` + `service-worker.js` ada |

---

## 🔒 .gitignore (Rekomendasi)

Agar repo bersih, buat file `.gitignore`:

```gitignore
# Python
__pycache__/
*.pyc
*.pyo
.venv/
venv/

# SSL (dibuat otomatis, jangan di-commit)
cert.pem
key.pem

# Node.js (tidak dipakai, tapi aman untuk di-ignore)
node_modules/
package-lock.json

# OS
.DS_Store
Thumbs.db
```

---

## 🛠️ Tips Tambahan

- **Ganti port:** Edit `PORT = 8443` di `server.py`, lalu akses `https://<IP>:<port-baru>`
- **Matikan server dengan rapi:** Ketik `/exit` di CMD (lebih aman daripada menutup CMD paksa)
- **Cek IP laptop:** `ipconfig` di CMD, lihat bagian `IPv4 Address`
- **QR Code hilang?** Ketik `/qr` untuk menampilkannya lagi

---

## 📄 Lisensi

MIT License — bebas digunakan dan dimodifikasi.

---

**Selamat bertempur di lapangan! 🎙️🖥️**
