import asyncio
import os
import socket
import json
import ssl
import qrcode
import uuid
from datetime import datetime
from aiohttp import web
from OpenSSL import crypto

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

os.chdir(os.path.dirname(os.path.abspath(__file__)))

clients = {}       
rooms = {}         
sessions = {}      
busy_rooms = {}    

admin_listen_target = {"name": None, "channel": None} 
chat_history = [] 
ptt_history = [] 
URL_AKSES = ""
server_runner = None
server_site = None

async def index_handler(request):
    return web.FileResponse('./index.html')

async def clock_broadcaster():
    while True:
        await asyncio.sleep(1) 
        if rooms:
            time_str = datetime.now().strftime("%H:%M:%S")
            msg = {'type': 'server-time', 'time': time_str}
            for room_ws in rooms.values():
                for ws in room_ws:
                    try: await ws.send_json(msg)
                    except: pass

def print_admin_log(text):
    print(f"\r\033[K{text}")
    print("📢 Admin > ", end="", flush=True)

async def send_to_channel(room_id, msg):
    if room_id in rooms:
        for ws in rooms[room_id]:
            try: await ws.send_json(msg)
            except: pass

async def send_to_target(target_name, target_channel, msg):
    found = 0
    for ws, info in clients.items():
        if info['name'].lower() == target_name.lower() and str(info['room']) == str(target_channel):
            try: 
                await ws.send_json(msg)
                found += 1
            except: pass
    return found

async def kick_user(target_name, target_channel=None):
    found_count = 0
    for ws, info in list(clients.items()):
        match_channel = (target_channel is None) or (str(info['room']) == str(target_channel))
        
        if info['name'].lower() == target_name.lower() and match_channel:
            found_count += 1
            room_id = info['room']
            print_admin_log(f"🚫 [KICK] Menendang {info['name']} dari Channel #{room_id}...")
            
            await ws.close(code=4001, message=b'Kicked by Admin')
            
            kick_msg = {
                'type': 'chat-message', 
                'id': 'system', 
                'name': 'SISTEM', 
                'text': f'⚠️ {info["name"]} telah dikeluarkan oleh Pusat Komando.'
            }
            await send_to_channel(room_id, kick_msg)
            
    if found_count == 0:
        print_admin_log(f"❌ [KICK] Pengguna '{target_name}' tidak ditemukan.")
    else:
        print_admin_log(f"✅ [KICK] {found_count} pengguna bernama '{target_name}' berhasil ditendang.")

async def kick_channel(target_channel):
    found_count = 0
    if target_channel in rooms:
        for ws in list(rooms[target_channel]):
            info = clients.get(ws)
            if info:
                found_count += 1
                print_admin_log(f"🚫 [KICK] Menendang {info['name']} dari Channel #{target_channel}...")
                await ws.close(code=4001, message=b'Kicked by Admin')
        
        kick_msg = {
            'type': 'chat-message', 
            'id': 'system', 
            'name': 'SISTEM', 
            'text': f'⚠️ SELURUH ANGGOTA telah dikeluarkan oleh Pusat Komando.'
        }
        await send_to_channel(target_channel, kick_msg)
    
    if found_count == 0:
        print_admin_log(f"❌ [KICK] Tidak ada pengguna di Channel #{target_channel}.")
    else:
        print_admin_log(f"✅ [KICK] {found_count} pengguna di Channel #{target_channel} berhasil ditendang.")

def tampilkan_qr():
    qr = qrcode.QRCode(version=1, box_size=1, border=2)
    qr.add_data(URL_AKSES)
    qr.make(fit=True)
    print("\n" + "="*50)
    print("   🎙️ SCAN QR CODE INI:")
    print("="*50 + "\n")
    qr.print_ascii(invert=True)
    print("\n" + "="*50)
    print(f"   Atau ketik manual: {URL_AKSES}")
    print("="*50 + "\n")

async def cmd_chat_reader():
    global admin_listen_target, server_runner, server_site
    os.system('cls' if os.name == 'nt' else 'clear')
    print("="*60)
    print("🖥️  PUSAT KOMANDO (ADMIN) AKTIF")
    print("="*60)
    print("Ketik /help untuk melihat daftar perintah.")
    print("CATATAN: Ketik /exit atau tekan Ctrl+C untuk mematikan server.")
    print("="*60 + "\n")
    
    tampilkan_qr()

    while True:
        try:
            text = await asyncio.get_event_loop().run_in_executor(None, input, "📢 Admin > ")
            
            if not text.strip(): continue
            cmd_lower = text.strip().lower()
            parts = text.strip().split(' ', 3)

            if cmd_lower == '/exit':
                print("\n\n🛑 Mematikan server...")
                if server_site: await server_site.stop()
                if server_runner: await server_runner.cleanup()
                print("✅ Server berhasil dimatikan. Sampai jumpa!")
                os._exit(0)

            if cmd_lower == '/qr':
                tampilkan_qr()
                continue

            if cmd_lower == '/help':
                print("\n" + "-"*60)
                print("🛠️  DAFTAR PERINTAH ADMIN:")
                print("  /qr                                 -> Tampilkan QR Code")
                print("  /clear                              -> Bersihkan layar CMD")
                print("  /exit                               -> Matikan Server (Rapi)")
                print("  /listen <nomor>                     -> Pantau 1 channel")
                print("  /listen <nomor> <nama>              -> Pantau 1 orang")
                print("  /listen all                         -> Pantau semua channel")
                print("  /listenhistory <nomor>              -> Riwayat chat 1 channel")
                print("  /listenhistory <nomor> <nama>       -> Riwayat chat 1 orang")
                print("  /listenhistory all                  -> Riwayat chat semua channel")
                print("  /pttlog <nomor>                     -> Rekap PTT per channel")
                print("  /pttlog <nomor> <nama>              -> Rekap PTT 1 orang")
                print("  /pttlog all                         -> Rekap PTT semua channel")
                print("  /chat <nomor> <pesan>               -> Chat ke 1 channel")
                print("  /chat <nomor> <nama> <pesan>        -> Chat ke 1 orang")
                print("  /ring <nomor>                       -> Alarm ke 1 channel")
                print("  /ring <nomor> <nama>                -> Alarm ke 1 orang")
                print("  /users <nomor>                      -> Lihat pengguna 1 channel")
                print("  /users all                          -> Lihat semua pengguna")
                print("  /kick <nomor>                       -> Tendang semua orang di channel")
                print("  /kick <nomor> <nama>                -> Tendang 1 orang")
                print("-"*60 + "\n")
                continue

            if cmd_lower == '/clear':
                os.system('cls' if os.name == 'nt' else 'clear')
                print("="*60)
                print("🖥️  PUSAT KOMANDO (ADMIN) AKTIF")
                print("="*60)
                continue

            # FITUR PTT LOG
            if cmd_lower.startswith('/pttlog'):
                args = text.strip().split(' ')
                if len(args) == 1 or (len(args) == 2 and args[1].lower() == 'all'):
                    print("\n" + "-"*50)
                    print("🎙️  REKAP HISTORY PTT: SEMUA CHANNEL")
                    print("-" * 50)
                    if not ptt_history: print("  (Belum ada aktivitas PTT)")
                    for h in ptt_history:
                        print(f"  [{h['time']}] {h['name']} | MULAI BICARA (Ch #{h['channel']})")
                    print("-" * 50 + "\n")
                elif len(args) >= 3:
                    t_channel = str(args[1])
                    t_name = args[2].lower()
                    print("\n" + "-"*50)
                    print(f"🎙️  REKAP HISTORY PTT: {args[2]} (Channel #{t_channel})")
                    print("-" * 50)
                    found = False
                    for h in ptt_history:
                        if h['name'].lower() == t_name and str(h['channel']) == t_channel:
                            print(f"  [{h['time']}] {h['name']} | MULAI BICARA")
                            found = True
                    if not found: print("  (Belum ada aktivitas PTT)")
                    print("-" * 50 + "\n")
                elif len(args) == 2:
                    t_channel = str(args[1])
                    print("\n" + "-"*50)
                    print(f"🎙️  REKAP HISTORY PTT: Channel #{t_channel}")
                    print("-" * 50)
                    found = False
                    for h in ptt_history:
                        if str(h['channel']) == t_channel:
                            print(f"  [{h['time']}] {h['name']} | MULAI BICARA")
                            found = True
                    if not found: print("  (Belum ada aktivitas PTT)")
                    print("-" * 50 + "\n")
                else:
                    print("❌ Format: /pttlog <nomor> [nama] atau /pttlog all")
                continue

            # FITUR LISTEN
            if cmd_lower.startswith('/listen '):
                args = text.strip().split(' ')
                if args[1].lower() == 'all':
                    admin_listen_target = {"name": None, "channel": None}
                    print("👁️  [FILTER] Memantau SEMUA CHANNEL.")
                elif len(args) >= 3:
                    admin_listen_target = {"name": args[2].lower(), "channel": str(args[1])}
                    print(f"👁️  [FILTER] Hanya memantau '{args[2]}' di Channel #{args[1]}.")
                elif len(args) == 2:
                    admin_listen_target = {"name": None, "channel": str(args[1])}
                    print(f"👁️  [FILTER] Memantau CHANNEL #{args[1]}.")
                else:
                    print("❌ Format: /listen <nomor> [nama] atau /listen all")
                continue

            # FITUR LISTEN HISTORY
            if cmd_lower.startswith('/listenhistory '):
                args = text.strip().split(' ')
                if args[1].lower() == 'all':
                    print("\n" + "-"*50)
                    print("🕵️  RIWAYAT CHAT: SEMUA CHANNEL")
                    print("-" * 50)
                    found = False
                    for h in chat_history:
                        print(f"  [Ch {h['channel']}] [{h['time']}] {h['name']}: {h['text']}")
                        found = True
                    if not found: print("  (Belum ada obrolan)")
                    print("-" * 50 + "\n")
                elif len(args) >= 3:
                    t_channel = str(args[1])
                    t_name = args[2].lower()
                    print("\n" + "-"*50)
                    print(f"🕵️  RIWAYAT CHAT: {args[2]} (Channel #{t_channel})")
                    print("-" * 50)
                    found = False
                    for h in chat_history:
                        if h['name'].lower() == t_name and str(h['channel']) == t_channel:
                            print(f"  [{h['time']}] {h['name']}: {h['text']}")
                            found = True
                    if not found: print("  (Belum ada obrolan)")
                    print("-" * 50 + "\n")
                elif len(args) == 2:
                    t_channel = str(args[1])
                    print("\n" + "-"*50)
                    print(f"🕵️  RIWAYAT CHAT: Channel #{t_channel}")
                    print("-" * 50)
                    found = False
                    for h in chat_history:
                        if str(h['channel']) == t_channel:
                            print(f"  [{h['time']}] {h['name']}: {h['text']}")
                            found = True
                    if not found: print("  (Belum ada obrolan)")
                    print("-" * 50 + "\n")
                else:
                    print("❌ Format: /listenhistory <nomor> [nama] atau /listenhistory all")
                continue

            # FITUR USERS
            if cmd_lower.startswith('/users'):
                args = text.strip().split(' ')
                target_channel = None
                if len(args) > 1 and args[1].lower() != 'all': target_channel = args[1]
                
                print("\n" + "-"*40)
                print("👥 DAFTAR PENGGUNA:")
                found = False
                for ws, info in clients.items():
                    if target_channel is None or str(info['room']) == str(target_channel):
                        print(f"  - {info['name']} (Channel #{info['room']})")
                        found = True
                if not found: print("  (Tidak ada pengguna)")
                print("-" * 40 + "\n")
                continue

            # FITUR KICK
            if cmd_lower.startswith('/kick '):
                args = text.strip().split(' ')
                if len(args) >= 3:
                    await kick_user(args[2], args[1])
                elif len(args) == 2:
                    await kick_channel(args[1])
                else:
                    print("❌ Format: /kick <nomor> atau /kick <nomor> <nama>")
                continue

            # FITUR RING
            if cmd_lower.startswith('/ring'):
                args = text.strip().split(' ')
                msg = {'type': 'receive-buzzer', 'id': 'admin', 'name': '📢 PUSAT KOMANDO'}
                
                if len(args) >= 3:
                    sent = await send_to_target(args[2], args[1], msg)
                    if sent > 0: print(f"🚨 [ALARM] Ring terkirim ke {args[2]} di Ch #{args[1]}.")
                    else: print(f"❌ Pengguna {args[2]} tidak ditemukan.")
                elif len(args) == 2:
                    await send_to_channel(args[1], msg)
                    print(f"🚨 [ALARM] Ring terkirim ke SEMUA orang di Channel #{args[1]}.")
                else:
                    for room_id in rooms: await send_to_channel(room_id, msg)
                    print("🚨 [ALARM] Ring disiarkan ke SEMUA channel!")
                continue

            # FITUR CHAT
            if cmd_lower.startswith('/chat '):
                if len(parts) >= 4:
                    target_channel = parts[1]
                    target_name = parts[2]
                    pesan = parts[3]
                    msg = {'type': 'chat-message', 'id': 'admin', 'name': '📢 PUSAT KOMANDO', 'text': pesan}
                    sent = await send_to_target(target_name, target_channel, msg)
                    if sent > 0: print(f"✅ [CHAT ADMIN] Terkirim privat ke {target_name}.")
                    else: print(f"❌ Pengguna {target_name} tidak ditemukan.")
                elif len(parts) == 3:
                    target_channel = parts[1]
                    pesan = parts[2]
                    msg = {'type': 'chat-message', 'id': 'admin', 'name': '📢 PUSAT KOMANDO', 'text': pesan}
                    await send_to_channel(target_channel, msg)
                    print(f"✅ [CHAT ADMIN] Terkirim ke Channel #{target_channel}.")
                else:
                    print("❌ Format: /chat <nomor> [nama] <pesan>")
                continue

            # PESAN BIASA (BROADCAST)
            msg = {'type': 'chat-message', 'id': 'admin', 'name': '📢 PUSAT KOMANDO', 'text': text}
            for room_id in rooms: await send_to_channel(room_id, msg)
            print(f"✅ [CHAT ADMIN] Broadcast terkirim ke semua channel.")
            
        except KeyboardInterrupt:
            # TANGKAP SINYAL CTRL+C DI SINI
            print("\n\n🛑 Ctrl+C ditekan. Mematikan server secara paksa...")
            os._exit(0)
        except Exception:
            break

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    client_id = str(id(ws))
    client_room = None
    client_name = "Anonim"

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                data = json.loads(msg.data)
                
                if data['type'] == 'join':
                    session_id = data.get('session_id')
                    if session_id and session_id in sessions:
                        client_room = sessions[session_id]['room']
                        client_name = sessions[session_id]['name']
                    else:
                        session_id = str(uuid.uuid4())[:8]
                        client_room = data['room']
                        client_name = data['name']
                        sessions[session_id] = {'name': client_name, 'room': client_room}

                    await ws.send_json({'type': 'session_created', 'session_id': session_id})
                    current_time = datetime.now().strftime("%H:%M:%S")
                    await ws.send_json({'type': 'server-time', 'time': current_time})
                    clients[ws] = {'id': client_id, 'room': client_room, 'name': client_name}
                    
                    if client_room not in rooms:
                        rooms[client_room] = []
                        busy_rooms[client_room] = False

                    current_users = []
                    for other_ws in rooms[client_room]:
                        info = clients.get(other_ws)
                        if info: current_users.append({'id': info['id'], 'name': info['name']})
                    
                    await ws.send_json({'type': 'user-list', 'users': current_users})
                    await ws.send_json({'type': 'channel_status', 'busy': busy_rooms[client_room]})
                    
                    for other_ws in rooms[client_room]:
                        await other_ws.send_json({'type': 'peer-joined', 'id': client_id, 'name': client_name})
                    rooms[client_room].append(ws)

                    is_target = (admin_listen_target['name'] is None and admin_listen_target['channel'] is None) or \
                                (admin_listen_target['name'] is None and str(client_room) == admin_listen_target['channel']) or \
                                (client_name.lower() == admin_listen_target['name'] and str(client_room) == admin_listen_target['channel'])
                    if is_target: print_admin_log(f"🟢 [MASUK] {client_name} bergabung ke Channel #{client_room}")

                elif data['type'] == 'signal':
                    target_id = data['target']
                    for target_ws, info in clients.items():
                        if info['id'] == target_id:
                            await target_ws.send_json({
                                'type': 'signal', 'id': client_id,
                                'sdp': data.get('sdp'), 'candidate': data.get('candidate')
                            })
                            break
                            
                elif data['type'] == 'request-talk':
                    if client_room and not busy_rooms.get(client_room, False):
                        busy_rooms[client_room] = True
                        await ws.send_json({'type': 'talk-granted'})
                        for other_ws in rooms[client_room]:
                            if other_ws != ws:
                                await other_ws.send_json({'type': 'talk-start', 'id': client_id, 'name': client_name})
                        
                        now = datetime.now().strftime("%H:%M:%S")
                        ptt_history.append({'name': client_name, 'channel': client_room, 'time': now})
                        if len(ptt_history) > 1000: ptt_history.pop(0)

                        is_target = (admin_listen_target['name'] is None and admin_listen_target['channel'] is None) or \
                                    (admin_listen_target['name'] is None and str(client_room) == admin_listen_target['channel']) or \
                                    (client_name.lower() == admin_listen_target['name'] and str(client_room) == admin_listen_target['channel'])
                        if is_target: print_admin_log(f"🎙️ [PTT] {client_name} sedang bicara (Ch #{client_room})")
                    else:
                        await ws.send_json({'type': 'talk-denied'})

                elif data['type'] == 'release-talk':
                    if client_room and busy_rooms.get(client_room, False):
                        busy_rooms[client_room] = False
                        for other_ws in rooms[client_room]:
                            if other_ws != ws:
                                await other_ws.send_json({'type': 'talk-stop', 'id': client_id})
                        
                        is_target = (admin_listen_target['name'] is None and admin_listen_target['channel'] is None) or \
                                    (admin_listen_target['name'] is None and str(client_room) == admin_listen_target['channel']) or \
                                    (client_name.lower() == admin_listen_target['name'] and str(client_room) == admin_listen_target['channel'])
                        if is_target: print_admin_log(f"🔇 [PTT] {client_name} selesai bicara (Ch #{client_room})")

                elif data['type'] == 'chat-message':
                    if client_room in rooms:
                        for other_ws in rooms[client_room]:
                            await other_ws.send_json({
                                'type': 'chat-message', 'id': client_id,
                                'name': client_name, 'text': data['text']
                            })
                        
                        now = datetime.now().strftime("%H:%M:%S")
                        chat_history.append({'name': client_name, 'channel': client_room, 'text': data['text'], 'time': now})
                        if len(chat_history) > 1000: chat_history.pop(0)
                        
                        is_target = (admin_listen_target['name'] is None and admin_listen_target['channel'] is None) or \
                                    (admin_listen_target['name'] is None and str(client_room) == admin_listen_target['channel']) or \
                                    (client_name.lower() == admin_listen_target['name'] and str(client_room) == admin_listen_target['channel'])
                        if is_target: print_admin_log(f"💬 [CHAT Ch #{client_room}] {client_name}: {data['text']}")

                elif data['type'] == 'send-buzzer':
                    if client_room in rooms:
                        for other_ws in rooms[client_room]:
                            if other_ws != ws:
                                await other_ws.send_json({
                                    'type': 'receive-buzzer', 'id': client_id, 'name': client_name
                                })
                        
                        is_target = (admin_listen_target['name'] is None and admin_listen_target['channel'] is None) or \
                                    (admin_listen_target['name'] is None and str(client_room) == admin_listen_target['channel']) or \
                                    (client_name.lower() == admin_listen_target['name'] and str(client_room) == admin_listen_target['channel'])
                        if is_target: print_admin_log(f"🔔 [BUZZER] {client_name} memanggil (Ch #{client_room})")

    except Exception:
        pass
    finally:
        if ws in clients:
            info = clients[ws]
            del clients[ws]
            if info['room'] in rooms and ws in rooms[info['room']]:
                rooms[info['room']].remove(ws)
                if busy_rooms.get(info['room'], False): busy_rooms[info['room']] = False
                for other_ws in rooms[info['room']]:
                    try: await other_ws.send_json({'type': 'peer-left', 'id': client_id})
                    except: pass
            
            is_target = (admin_listen_target['name'] is None and admin_listen_target['channel'] is None) or \
                        (admin_listen_target['name'] is None and str(info['room']) == admin_listen_target['channel']) or \
                        (info['name'].lower() == admin_listen_target['name'] and str(info['room']) == admin_listen_target['channel'])
            if is_target: print_admin_log(f"❌ [KELUAR] {info['name']} terputus dari Channel #{info['room']}.")
    return ws

async def init_app():
    app = web.Application()
    app.router.add_get('/', index_handler)
    app.router.add_get('/ws', websocket_handler)
    return app

def buat_sertifikat(my_ip):
    if not os.path.exists("cert.pem") or not os.path.exists("key.pem"):
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 2048)
        cert = crypto.X509()
        cert.get_subject().CN = my_ip
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(315360000)
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(k)
        cert.sign(k, 'sha256')
        with open("cert.pem", "wb") as f: f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        with open("key.pem", "wb") as f: f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))

async def main():
    global URL_AKSES, server_runner, server_site
    my_ip = get_ip()
    PORT = 8443
    URL_AKSES = f"https://{my_ip}:{PORT}"
    buat_sertifikat(my_ip)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('cert.pem', 'key.pem')
    
    app = await init_app()
    server_runner = web.AppRunner(app)
    await server_runner.setup()
    
    asyncio.create_task(clock_broadcaster())
    asyncio.create_task(cmd_chat_reader())
    
    server_site = web.TCPSite(server_runner, '0.0.0.0', PORT, ssl_context=context)
    await server_site.start()
    
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Program dihentikan (Ctrl+C).")
        os._exit(0)