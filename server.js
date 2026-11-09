const express = require('express');
const https = require('https');
const { ExpressPeerServer } = require('peer');
const selfsigned = require('selfsigned');
const os = require('os');
const path = require('path');

// ============================================================
// 1. GENERATE SELF-SIGNED CERT (auto, tanpa OpenSSL manual)
// ============================================================
console.log('🔐 Membuat sertifikat SSL...');
const attrs = [{ name: 'commonName', value: 'intratalk.local' }];
const pems = selfsigned.generate(attrs, {
  days: 365,
  keySize: 2048,
  algorithm: 'sha256',
  extensions: [{
    name: 'subjectAltName',
    altNames: [
      { type: 2, value: 'localhost' },
      { type: 7, ip: '127.0.0.1' },
      // Tambahkan IP LAN Anda di sini jika perlu, misal:
      // { type: 7, ip: '192.168.1.100' }
    ]
  }]
});

// ============================================================
// 2. EXPRESS APP + STATIC FILES
// ============================================================
const app = express();
app.use(express.static(path.join(__dirname, 'public')));

// ============================================================
// 3. HTTPS SERVER
// ============================================================
const server = https.createServer(
  { key: pems.private, cert: pems.cert },
  app
);

// ============================================================
// 4. PEERJS SIGNALING SERVER (di path /myapp)
// ============================================================
const peerServer = ExpressPeerServer(server, {
  path: '/myapp',
  allow_discovery: true,
  proxied: true
});
app.use('/myapp', peerServer);

// Log koneksi peer
peerServer.on('connection', (client) => {
  console.log(`🟢 Peer terhubung: ${client.getId()}`);
});
peerServer.on('disconnect', (client) => {
  console.log(`🔴 Peer keluar: ${client.getId()}`);
});

// ============================================================
// 5. START & TAMPILKAN INFO AKSES
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

  console.log('\n═══════════════════════════════════════════════');
  console.log('   🎙️  INTRATALK SERVER AKTIF');
  console.log('═══════════════════════════════════════════════');
  console.log(`   Port       : ${PORT}`);
  console.log(`   Signaling  : /myapp`);
  console.log('───────────────────────────────────────────────');
  console.log('   Buka di HP (satu Wi-Fi):');
  ips.forEach(ip => {
    console.log(`   👉  https://${ip}:${PORT}`);
  });
  console.log('───────────────────────────────────────────────');
  console.log('   ⚠️  Browser akan peringatkan "not secure".');
  console.log('       Klik "Advanced" → "Proceed" untuk lanjut.');
  console.log('   ⚠️  Pastikan firewall laptop mengizinkan');
  console.log(`       koneksi masuk ke port ${PORT}.`);
  console.log('═══════════════════════════════════════════════\n');
});
