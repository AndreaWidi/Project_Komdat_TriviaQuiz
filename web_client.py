"""
TRIVIA QUIZ MULTIPLAYER - WEB SERVER (Bridge)
Komunikasi Data 2026

Flask + Flask-SocketIO sebagai jembatan antara browser dan TCP server.
Browser <-- WebSocket --> Flask Bridge <-- TCP --> Game Server
"""

from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit
import socket
import threading
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'triviaquiz2026'
socketio = SocketIO(app, cors_allowed_origins="*")

TCP_HOST = '172.20.10.2'
TCP_PORT = 5555

# Simpan koneksi TCP per session
tcp_connections = {}  # {sid: socket}

# ─── HTML TEMPLATE ────────────────────────────────────────────────────────────
HTML = """
<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Trivia Quiz Multiplayer</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Segoe UI', sans-serif;
      background: #0f172a;
      color: #e2e8f0;
      min-height: 100vh;
    }

    /* ─── HEADER ─── */
    .header {
      background: linear-gradient(135deg, #1e3a5f 0%, #0f2744 100%);
      padding: 16px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid #1e40af;
    }
    .header h1 {
      font-size: 22px;
      color: #60a5fa;
      font-weight: 700;
    }
    .header span { font-size: 13px; color: #94a3b8; }

    /* ─── LAYOUT ─── */
    .layout {
      display: grid;
      grid-template-columns: 1fr 280px;
      gap: 0;
      height: calc(100vh - 64px);
    }

    /* ─── MAIN AREA ─── */
    .main { padding: 24px; overflow-y: auto; }

    /* ─── SIDEBAR ─── */
    .sidebar {
      background: #1e293b;
      border-left: 1px solid #334155;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 16px;
      overflow-y: auto;
    }

    /* ─── CARDS ─── */
    .card {
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 16px;
    }
    .card h2 {
      font-size: 15px;
      color: #94a3b8;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 14px;
    }

    /* ─── LOBBY SCREEN ─── */
    #lobby { display: block; }
    #game-area { display: none; }

    .input-group {
      display: flex;
      gap: 10px;
      margin-bottom: 12px;
    }
    input[type="text"] {
      flex: 1;
      background: #0f172a;
      border: 1px solid #334155;
      border-radius: 8px;
      padding: 10px 14px;
      color: #e2e8f0;
      font-size: 14px;
      outline: none;
    }
    input[type="text"]:focus {
      border-color: #3b82f6;
    }
    input[type="text"]::placeholder { color: #475569; }

    .btn {
      padding: 10px 20px;
      border: none;
      border-radius: 8px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }
    .btn-primary {
      background: #2563eb;
      color: white;
    }
    .btn-primary:hover { background: #1d4ed8; }
    .btn-success {
      background: #16a34a;
      color: white;
    }
    .btn-success:hover { background: #15803d; }
    .btn:disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }

    /* ─── SOAL ─── */
    .nomor-soal {
      font-size: 12px;
      color: #64748b;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 6px;
    }
    .teks-soal {
      font-size: 20px;
      font-weight: 600;
      color: #f1f5f9;
      line-height: 1.5;
      margin-bottom: 24px;
    }

    /* ─── PILIHAN ─── */
    .pilihan-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }
    .btn-pilihan {
      background: #0f172a;
      border: 2px solid #334155;
      border-radius: 10px;
      padding: 16px;
      color: #e2e8f0;
      font-size: 14px;
      cursor: pointer;
      text-align: left;
      transition: all 0.15s;
    }
    .btn-pilihan:hover:not(:disabled) {
      border-color: #3b82f6;
      background: #1e3a5f;
    }
    .btn-pilihan:disabled { cursor: not-allowed; opacity: 0.5; }
    .btn-pilihan.dipilih {
      border-color: #3b82f6;
      background: #1e3a5f;
    }

    /* ─── TIMER ─── */
    .timer-wrap {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 20px;
    }
    .timer-bar-wrap {
      flex: 1;
      height: 6px;
      background: #1e293b;
      border-radius: 4px;
      overflow: hidden;
    }
    .timer-bar {
      height: 100%;
      background: #3b82f6;
      border-radius: 4px;
      transition: width 1s linear, background 0.5s;
    }
    .timer-angka {
      font-size: 16px;
      font-weight: 700;
      color: #60a5fa;
      min-width: 40px;
      text-align: right;
    }

    /* ─── HASIL RONDE ─── */
    .hasil-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 12px;
      border-radius: 8px;
      margin-bottom: 6px;
      background: #0f172a;
    }
    .hasil-item.benar { border-left: 3px solid #22c55e; }
    .hasil-item.salah { border-left: 3px solid #ef4444; }
    .hasil-nama { font-weight: 600; font-size: 14px; }
    .hasil-skor { font-size: 13px; color: #94a3b8; }

    /* ─── PAPAN SKOR ─── */
    .skor-item {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 8px 0;
      border-bottom: 1px solid #1e293b;
    }
    .skor-rank { font-size: 18px; min-width: 28px; }
    .skor-nama { flex: 1; font-size: 14px; font-weight: 500; }
    .skor-poin {
      font-size: 15px;
      font-weight: 700;
      color: #fbbf24;
    }
    .saya-tag {
      font-size: 11px;
      background: #1e40af;
      color: #93c5fd;
      padding: 1px 6px;
      border-radius: 4px;
    }

    /* ─── CHAT ─── */
    .chat-box {
      height: 180px;
      overflow-y: auto;
      background: #0f172a;
      border-radius: 8px;
      padding: 10px;
      margin-bottom: 10px;
      font-size: 13px;
    }
    .chat-msg { margin-bottom: 4px; }
    .chat-dari { color: #60a5fa; font-weight: 600; }
    .chat-input-wrap { display: flex; gap: 6px; }
    .chat-input {
      flex: 1;
      background: #0f172a;
      border: 1px solid #334155;
      border-radius: 6px;
      padding: 7px 10px;
      color: #e2e8f0;
      font-size: 13px;
    }
    .btn-chat {
      background: #2563eb;
      color: white;
      border: none;
      border-radius: 6px;
      padding: 7px 12px;
      cursor: pointer;
      font-size: 13px;
    }

    /* ─── LOG ─── */
    .log-box {
      height: 120px;
      overflow-y: auto;
      font-size: 12px;
      color: #64748b;
      background: #0f172a;
      border-radius: 8px;
      padding: 10px;
    }
    .log-msg { margin-bottom: 3px; }

    /* ─── NOTIF ─── */
    .notif {
      padding: 10px 14px;
      border-radius: 8px;
      margin-bottom: 10px;
      font-size: 13px;
      display: none;
    }
    .notif.info { background: #1e3a5f; border: 1px solid #1e40af; color: #93c5fd; display: block; }
    .notif.sukses { background: #14532d; border: 1px solid #166534; color: #86efac; display: block; }
    .notif.error { background: #450a0a; border: 1px solid #7f1d1d; color: #fca5a5; display: block; }

    /* ─── PEMAIN LIST ─── */
    .pemain-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 6px 0;
      font-size: 13px;
    }
    .dot { width: 8px; height: 8px; border-radius: 50%; background: #22c55e; }

    /* ─── RESPONSIVE ─── */
    @media (max-width: 640px) {
      .layout { grid-template-columns: 1fr; }
      .sidebar { display: none; }
      .pilihan-grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>

<div class="header">
  <h1>🎯 Trivia Quiz Multiplayer</h1>
  <span id="status-header">Belum terhubung</span>
</div>

<div class="layout">
  <!-- MAIN CONTENT -->
  <div class="main">
    <div id="notif" class="notif"></div>

    <!-- LOBBY -->
    <div id="lobby">
      <div class="card">
        <h2>Bergabung ke Server</h2>
        <div class="input-group">
          <input type="text" id="nama-input" placeholder="Nama pemain kamu..." maxlength="20">
          <button class="btn btn-primary" onclick="bergabung()">Gabung</button>
        </div>
        <p style="font-size: 13px; color: #64748b;">
          Server: <span style="color: #60a5fa">{{ host }}:{{ port }}</span>
        </p>
      </div>

      <div class="card" id="lobby-info" style="display:none">
        <h2>Lobby</h2>
        <p style="font-size: 13px; color: #94a3b8; margin-bottom: 14px;">
          Tunggu semua pemain bergabung, lalu tekan Mulai Game.
        </p>
        <button class="btn btn-success" onclick="mulaiGame()" id="btn-mulai">
          🚀 Mulai Game
        </button>
      </div>
    </div>

    <!-- GAME AREA -->
    <div id="game-area">
      <!-- Soal -->
      <div class="card" id="soal-card" style="display:none">
        <div class="nomor-soal" id="nomor-soal">Soal 1 / 10</div>
        <div class="teks-soal" id="teks-soal">Loading...</div>
        <div class="timer-wrap">
          <div class="timer-bar-wrap">
            <div class="timer-bar" id="timer-bar" style="width:100%"></div>
          </div>
          <div class="timer-angka" id="timer-angka">15</div>
        </div>
        <div class="pilihan-grid" id="pilihan-grid"></div>
      </div>

      <!-- Hasil Ronde -->
      <div class="card" id="hasil-card" style="display:none">
        <h2>Hasil Ronde</h2>
        <div style="margin-bottom: 12px; padding: 10px 14px; background: #14532d; border-radius: 8px; font-size: 14px; color: #86efac;">
          ✅ Jawaban benar: <strong id="jwb-benar"></strong>
        </div>
        <div id="hasil-list"></div>
      </div>

      <!-- Game Selesai -->
      <div class="card" id="selesai-card" style="display:none">
        <h2 style="text-align:center; font-size:20px; color:#fbbf24; margin-bottom: 20px;">
          🏆 GAME SELESAI!
        </h2>
        <div id="papan-skor"></div>
        <button class="btn btn-primary" style="width:100%; margin-top:16px" onclick="location.reload()">
          Main Lagi
        </button>
      </div>
    </div>
  </div>

  <!-- SIDEBAR -->
  <div class="sidebar">
    <!-- Pemain -->
    <div>
      <h2 style="font-size:12px; color:#475569; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:10px">
        👥 Pemain Online
      </h2>
      <div id="pemain-list">
        <p style="font-size: 12px; color: #475569;">Belum ada pemain...</p>
      </div>
    </div>

    <!-- Skor Sementara -->
    <div>
      <h2 style="font-size:12px; color:#475569; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:10px">
        📊 Skor Sementara
      </h2>
      <div id="skor-sementara">
        <p style="font-size: 12px; color: #475569;">Game belum dimulai</p>
      </div>
    </div>

    <!-- Chat -->
    <div style="flex:1">
      <h2 style="font-size:12px; color:#475569; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:10px">
        💬 Chat
      </h2>
      <div class="chat-box" id="chat-box"></div>
      <div class="chat-input-wrap">
        <input type="text" class="chat-input" id="chat-input" placeholder="Pesan..." maxlength="100"
               onkeydown="if(event.key==='Enter') kirimChat()">
        <button class="btn-chat" onclick="kirimChat()">➤</button>
      </div>
    </div>

    <!-- Log -->
    <div>
      <h2 style="font-size:12px; color:#475569; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:6px">
        📡 Log
      </h2>
      <div class="log-box" id="log-box"></div>
    </div>
  </div>
</div>

<script>
  const socket = io();
  let namaSaya = "";
  let waktuSoal = 15;
  let jawabDikirim = false;

  // ── NOTIFIKASI ────────────────────────────────────────────────────────────
  function tampilNotif(pesan, tipe="info") {
    const el = document.getElementById("notif");
    el.className = "notif " + tipe;
    el.textContent = pesan;
    if (tipe === "sukses") setTimeout(() => { el.style.display = "none"; }, 3000);
  }

  function tambahLog(pesan) {
    const box = document.getElementById("log-box");
    const div = document.createElement("div");
    div.className = "log-msg";
    div.textContent = new Date().toLocaleTimeString("id") + " — " + pesan;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
  }

  // ── BERGABUNG ────────────────────────────────────────────────────────────
  function bergabung() {
    namaSaya = document.getElementById("nama-input").value.trim();
    if (!namaSaya) { tampilNotif("Masukkan nama dulu!", "error"); return; }
    socket.emit("gabung", { nama: namaSaya });
  }

  function mulaiGame() {
    socket.emit("mulai");
  }

  // ── JAWAB ─────────────────────────────────────────────────────────────────
  function jawab(huruf) {
    if (jawabDikirim) return;
    jawabDikirim = true;
    socket.emit("jawab", { jawaban: huruf });
    document.querySelectorAll(".btn-pilihan").forEach(b => b.disabled = true);
    document.querySelectorAll(".btn-pilihan").forEach(b => {
      if (b.dataset.huruf === huruf) b.classList.add("dipilih");
    });
  }

  // ── CHAT ──────────────────────────────────────────────────────────────────
  function kirimChat() {
    const inp = document.getElementById("chat-input");
    const pesan = inp.value.trim();
    if (!pesan) return;
    socket.emit("chat", { pesan });
    inp.value = "";
  }

  // ── UPDATE PEMAIN LIST ────────────────────────────────────────────────────
  function updatePemainList(pemain) {
    const el = document.getElementById("pemain-list");
    el.innerHTML = pemain.map(p =>
      `<div class="pemain-item">
         <div class="dot"></div>
         <span>${p}${p === namaSaya ? ' <span class="saya-tag">kamu</span>' : ''}</span>
       </div>`
    ).join("");
  }

  // ── SOCKET EVENTS ─────────────────────────────────────────────────────────
  socket.on("gabung_ok", d => {
    document.getElementById("lobby-info").style.display = "block";
    document.getElementById("status-header").textContent = `✅ ${d.nama}`;
    tampilNotif(d.pesan, "sukses");
    tambahLog("Berhasil bergabung");
  });

  socket.on("info", d => {
    tambahLog(d.pesan);
  });

  socket.on("pemain_list", d => {
    updatePemainList(d.pemain);
    tambahLog(`Pemain: ${d.pemain.join(", ")}`);
  });

  socket.on("game_mulai", d => {
    document.getElementById("lobby").style.display = "none";
    document.getElementById("game-area").style.display = "block";
    tampilNotif(d.pesan, "sukses");
    tambahLog("Game dimulai!");
  });

  socket.on("soal", d => {
    jawabDikirim = false;
    waktuSoal = d.waktu;

    document.getElementById("soal-card").style.display = "block";
    document.getElementById("hasil-card").style.display = "none";
    document.getElementById("selesai-card").style.display = "none";

    document.getElementById("nomor-soal").textContent = `Soal ${d.nomor} / ${d.total}`;
    document.getElementById("teks-soal").textContent = d.soal;
    document.getElementById("timer-angka").textContent = d.waktu;
    document.getElementById("timer-bar").style.width = "100%";
    document.getElementById("timer-bar").style.background = "#3b82f6";

    const grid = document.getElementById("pilihan-grid");
    grid.innerHTML = d.pilihan.map(p => {
      const huruf = p[0];
      return `<button class="btn-pilihan" data-huruf="${huruf}" onclick="jawab('${huruf}')">
                ${p}
              </button>`;
    }).join("");

    tambahLog(`Soal ${d.nomor}: ${d.soal.substring(0, 40)}...`);
  });

  socket.on("timer", d => {
    const angka = document.getElementById("timer-angka");
    const bar = document.getElementById("timer-bar");
    if (angka) angka.textContent = d.sisa;
    if (bar) {
      const pct = (d.sisa / waktuSoal) * 100;
      bar.style.width = pct + "%";
      if (d.sisa <= 5) bar.style.background = "#ef4444";
      else if (d.sisa <= 10) bar.style.background = "#f59e0b";
    }
  });

  socket.on("jawab_ok", d => {
    tampilNotif("✔ " + d.pesan, "sukses");
  });

  socket.on("hasil_ronde", d => {
    document.getElementById("soal-card").style.display = "none";
    document.getElementById("hasil-card").style.display = "block";
    document.getElementById("jwb-benar").textContent = d.jawaban_benar;

    const list = document.getElementById("hasil-list");
    list.innerHTML = Object.entries(d.hasil).map(([nama, info]) =>
      `<div class="hasil-item ${info.benar ? 'benar' : 'salah'}">
         <div>
           <div class="hasil-nama">${nama}${nama === namaSaya ? ' <span class="saya-tag">kamu</span>' : ''}</div>
           <div style="font-size:12px; color:#94a3b8">${info.benar ? '✅' : '❌'} ${info.jawaban}</div>
         </div>
         <div class="hasil-skor">${info.skor} poin</div>
       </div>`
    ).join("");

    // Update skor sementara
    const skor = document.getElementById("skor-sementara");
    const sorted = Object.entries(d.hasil).sort((a,b) => b[1].skor - a[1].skor);
    skor.innerHTML = sorted.map(([nama, info], i) =>
      `<div class="skor-item">
         <span class="skor-rank">${['🥇','🥈','🥉'][i] || '#'+(i+1)}</span>
         <span class="skor-nama">${nama}</span>
         <span class="skor-poin">${info.skor}</span>
       </div>`
    ).join("");
  });

  socket.on("game_selesai", d => {
    document.getElementById("soal-card").style.display = "none";
    document.getElementById("hasil-card").style.display = "none";
    document.getElementById("selesai-card").style.display = "block";

    const medali = ["🥇","🥈","🥉"];
    document.getElementById("papan-skor").innerHTML = d.papan_skor.map((p, i) =>
      `<div class="skor-item">
         <span class="skor-rank">${medali[i] || '#'+(i+1)}</span>
         <span class="skor-nama">${p.nama}${p.nama === namaSaya ? ' <span class="saya-tag">kamu</span>' : ''}</span>
         <span class="skor-poin">${p.skor} poin</span>
       </div>`
    ).join("");

    tambahLog("Game selesai!");
  });

  socket.on("chat", d => {
    const box = document.getElementById("chat-box");
    const div = document.createElement("div");
    div.className = "chat-msg";
    div.innerHTML = `<span class="chat-dari">${d.dari}:</span> ${d.pesan}`;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
  });

  socket.on("error", d => {
    tampilNotif("❌ " + d.pesan, "error");
  });

  socket.on("connect", () => {
    document.getElementById("status-header").textContent = "Terhubung ke bridge";
    tambahLog("WebSocket terhubung");
  });
</script>
</body>
</html>
"""

# ─── SOCKETIO EVENTS ──────────────────────────────────────────────────────────
@socketio.on('connect')
def on_connect():
    print(f"[BRIDGE] Browser terhubung: {request.sid}")

@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    if sid in tcp_connections:
        try:
            tcp_connections[sid].close()
        except:
            pass
        del tcp_connections[sid]
    print(f"[BRIDGE] Browser putus: {sid}")

def tcp_listener(sid, sock):
    """Thread: dengarkan pesan dari TCP server, teruskan ke browser."""
    buffer = ""
    try:
        while True:
            data = sock.recv(4096).decode()
            if not data:
                break
            buffer += data
            while "\n" in buffer:
                baris, buffer = buffer.split("\n", 1)
                if not baris.strip():
                    continue
                try:
                    pesan = json.loads(baris)
                except:
                    continue
                tipe = pesan["tipe"].lower()
                socketio.emit(tipe, pesan["data"], to=sid)
    except:
        pass
    finally:
        socketio.emit("error", {"pesan": "Koneksi ke game server terputus"}, to=sid)

def kirim_tcp(sid, tipe, data={}):
    if sid not in tcp_connections:
        return
    pesan = json.dumps({"tipe": tipe, "data": data}) + "\n"
    try:
        tcp_connections[sid].sendall(pesan.encode())
    except:
        pass

@socketio.on('gabung')
def on_gabung(data):
    sid = request.sid
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((TCP_HOST, TCP_PORT))
        tcp_connections[sid] = sock

        t = threading.Thread(target=tcp_listener, args=(sid, sock), daemon=True)
        t.start()

        kirim_tcp(sid, "GABUNG", {"nama": data.get("nama", "Pemain")})
    except ConnectionRefusedError:
        emit("error", {"pesan": f"Tidak bisa terhubung ke game server ({TCP_HOST}:{TCP_PORT}). Pastikan server.py sudah berjalan!"})

@socketio.on('mulai')
def on_mulai():
    kirim_tcp(request.sid, "MULAI")

@socketio.on('jawab')
def on_jawab(data):
    kirim_tcp(request.sid, "JAWAB", data)

@socketio.on('chat')
def on_chat(data):
    kirim_tcp(request.sid, "CHAT", data)

# ─── ROUTE ────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template_string(HTML, host=TCP_HOST, port=TCP_PORT)

# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 50)
    print("  TRIVIA QUIZ WEB BRIDGE")
    print("=" * 50)
    print(f"[BRIDGE] Buka http://localhost:8080 di browser")
    print(f"[BRIDGE] Game server: {TCP_HOST}:{TCP_PORT}")
    print("[BRIDGE] Pastikan server.py sudah berjalan!")
    socketio.run(app, host='0.0.0.0', port=8080, debug=False, allow_unsafe_werkzeug=True)
