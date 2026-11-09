const https = require('https');
const express = require('express');
const { ExpressPeerServer } = require('peer');
const selfsigned = require('selfsigned');
const os = require('os');
const qrcode = require('qrcode-terminal');

// ============================================================
// 1. GENERATE CERT
// ============================================================
console.log('🔐 Membuat sertifikat SSL...');
const pems = selfsigned.generate(
  [{ name: 'commonName', value: 'intratalk.local' }],
  {
    days: 365,
    keySize: 2048,
    algorithm: 'sha256',
    extensions: [{
      name: 'subjectAltName',
      altNames: [
        { type: 2, value: 'localhost' },
        { type: 7, ip: '127.0.0.1' }
      ]
    }]
  }
);

// ============================================================
// 2. EXPRESS APP
// ============================================================
const app = express();

// CORS untuk GitHub Pages
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Headers', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  if (req.method === 'OPTIONS') return res.sendStatus(200);
  next();
});

// Health check endpoint (untuk test koneksi dari HP)
app.get('/', (req, res) => {
  res.send(`
    <h2>🎙️ IntraTalk Server Aktif</h2>
    <p>Server signaling walkie-talkie LAN.</p>
    <p>Kembali ke halaman walkie-talkie di GitHub Pages.</p>
  `);
});

// ============================================================
// 3. HTTPS SERVER
// ============================================================
const server = https.createServer(
  { key: pems.private, cert: pems.cert },
  app
);

// ============================================================
// 4. PEERJS SIGNALING
// ============================================================
const peerServer = ExpressPeerServer(server, {
  path: '/myapp',
  allow_discovery: true,
  proxied: true
});
app.use('/myapp', peerServer);

peerServer.on('connection', (client) => {
  console.log(`🟢 Peer terhubung: ${client.getId()}`);
});
peerServer.on('disconnect', (client) => {
  console.log(`🔴 Peer keluar: ${client.getId()}`);
});

// ============================================================
// 5. START + TAMPILKAN QR CODE
// ============================================================
const PORT = 8443;
server.listen(PORT, '0.0.0.0', () => {
  const nets = os.networkInterfaces();
  const ips = [];
  for (const name of Object.keys(nets)) {
    for (const net of nets[name]) {
      if (net.family === 'IPv4' && !net.internal) {
        ips.push(net.address);
      }
    }
  }

  console.log('\n═══════════════════════════════════════════════════════════');
  console.log('   🎙️  INTRATALK SERVER AKTIF');
  console.log('═══════════════════════════════════════════════════════════');
  console.log(`   Port       : ${PORT}`);
  console.log(`   Signaling  : /myapp`);
  console.log('───────────────────────────────────────────────────────────');

  if (ips.length === 0) {
    console.log('   ⚠️  Tidak ada IP LAN terdeteksi!');
    console.log('       Pastikan laptop terhubung ke Wi-Fi/LAN.');
  } else {
    ips.forEach((ip, idx) => {
      console.log(`\n   📡 Alamat Server #${idx + 1}: ${ip}`);
      console.log(`   👉  Scan QR berikut dari HP Anda:\n`);

      // QR berisi "IP:PORT" — format yang akan di-parse HP
      qrcode.generate(`${ip}:${PORT}`, { small: true });

      console.log(`\n   URL lengkap (jika perlu manual):`);
      console.log(`   https://${ip}:${PORT}\n`);
    });
  }

  console.log('───────────────────────────────────────────────────────────');
  console.log('   📱 Cara pakai:');
  console.log('      1. Buka halaman walkie-talkie di HP');
  console.log('      2. Klik tombol "Scan QR Server"');
  console.log('      3. Arahkan kamera ke QR di atas');
  console.log('      4. Isi nama & channel, lalu masuk');
  console.log('───────────────────────────────────────────────────────────');
  console.log('   ⚠️  Pastikan firewall mengizinkan port ' + PORT);
  console.log('   ⚠️  HP harus di Wi-Fi yang sama dengan laptop');
  console.log('═══════════════════════════════════════════════════════════\n');
});
