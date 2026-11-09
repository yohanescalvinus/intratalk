📦 1. Instal Python (Jika belum ada)
Jika di laptop Anda belum terinstal Python, jalankan perintah ini di CMD:

winget install Python.Python.3.12

PENTING: Setelah instalasi selesai, TUTUP CMD tersebut, lalu buka CMD baru. Ini wajib dilakukan agar Windows mengenali perintah Python.

📚 2. Instal Semua Library (Dependencies)
Di CMD yang baru, arahkan ke folder aplikasi Anda, lalu instal semua library yang dibutuhkan oleh server.py:

cd C:\intratalk
_(Sesuaikan C:\intratalk dengan lokasi folder aplikasi Anda)._

Kemudian jalankan perintah ini untuk mengunduh semua library:

pip install aiohttp pyopenssl qrcode

Penjelasan Library:
aiohttp: Untuk membuat server web HTTPS dan menangani koneksi WebSocket antar HP.
pyopenssl: Untuk membuat sertifikat SSL otomatis (agar HP mau mengizinkan akses mikrofon).
qrcode: Untuk menampilkan gambar QR Code di layar CMD laptop Anda.

🚀 3. Jalankan Server
Jika semua library sudah terinstal tanpa error, Anda bisa langsung menjalankan aplikasinya:

python server.py

Selesai! Server akan menyala, QR Code akan muncul, dan Anda siap bertempur di lapangan. 🎙️🖥️

