"""
TRIVIA QUIZ MULTIPLAYER - SERVER
Komunikasi Data 2026
TCP Server menggunakan Python socket
"""

import socket
import threading
import json
import time
import random

# ─── KONFIGURASI SERVER ───────────────────────────────────────────────────────
HOST = '172.20.10.2'
PORT = 5555
MAX_PLAYERS = 2
WAKTU_JAWAB = 15  # detik per soal

# ─── BANK SOAL ────────────────────────────────────────────────────────────────
BANK_SOAL = [
    {
        "soal": "Protokol apa yang digunakan untuk mengirim email?",
        "pilihan": ["A. HTTP", "B. SMTP", "C. FTP", "D. DNS"],
        "jawaban": "B"
    },
    {
        "soal": "Berapa layer dalam model OSI?",
        "pilihan": ["A. 5", "B. 6", "C. 7", "D. 8"],
        "jawaban": "C"
    },
    {
        "soal": "TCP singkatan dari?",
        "pilihan": ["A. Transfer Control Protocol", "B. Transmission Control Protocol",
                    "C. Transport Control Protocol", "D. Transmit Connection Protocol"],
        "jawaban": "B"
    },
    {
        "soal": "Port default untuk HTTP adalah?",
        "pilihan": ["A. 21", "B. 22", "C. 80", "D. 443"],
        "jawaban": "C"
    },
    {
        "soal": "UDP berbeda dari TCP karena?",
        "pilihan": ["A. Lebih lambat", "B. Connectionless / tanpa koneksi",
                    "C. Menggunakan IP berbeda", "D. Hanya untuk LAN"],
        "jawaban": "B"
    },
    {
        "soal": "Layer ke-4 dalam model OSI adalah?",
        "pilihan": ["A. Network", "B. Session", "C. Transport", "D. Data Link"],
        "jawaban": "C"
    },
    {
        "soal": "IP Address versi 6 (IPv6) memiliki panjang berapa bit?",
        "pilihan": ["A. 32 bit", "B. 64 bit", "C. 128 bit", "D. 256 bit"],
        "jawaban": "C"
    },
    {
        "soal": "Apa fungsi protokol DNS?",
        "pilihan": ["A. Mengirim file", "B. Mengubah nama domain ke IP address",
                    "C. Mengamankan koneksi", "D. Mengelola routing"],
        "jawaban": "B"
    },
    {
        "soal": "3-way handshake TCP terdiri dari?",
        "pilihan": ["A. SYN, ACK, FIN", "B. SYN, SYN-ACK, ACK",
                    "C. SYN, RST, ACK", "D. ACK, SYN, FIN"],
        "jawaban": "B"
    },
    {
        "soal": "Subnet mask untuk kelas C adalah?",
        "pilihan": ["A. 255.0.0.0", "B. 255.255.0.0", "C. 255.255.255.0", "D. 255.255.255.255"],
        "jawaban": "C"
    },
]

# ─── STATE GAME ───────────────────────────────────────────────────────────────
clients = {}         # {conn: {"nama": str, "skor": int, "sudah_jawab": bool}}
lock = threading.Lock()
game_berjalan = False
soal_sekarang = None
nomor_soal = 0
jawaban_ronde = {}   # {conn: jawaban}

# ─── FUNGSI KIRIM PESAN ───────────────────────────────────────────────────────
def kirim(conn, tipe, data):
    """Kirim pesan JSON ke satu client."""
    try:
        pesan = json.dumps({"tipe": tipe, "data": data}) + "\n"
        conn.sendall(pesan.encode())
    except:
        pass

def broadcast(tipe, data, kecuali=None):
    """Kirim pesan JSON ke semua client."""
    with lock:
        for conn in list(clients.keys()):
            if conn != kecuali:
                kirim(conn, tipe, data)

def broadcast_semua(tipe, data):
    """Kirim ke semua termasuk pengirim."""
    with lock:
        for conn in list(clients.keys()):
            kirim(conn, tipe, data)

# ─── LOGIKA GAME ──────────────────────────────────────────────────────────────
def kirim_soal():
    global soal_sekarang, nomor_soal, jawaban_ronde

    if nomor_soal >= len(BANK_SOAL):
        selesai_game()
        return

    soal_sekarang = BANK_SOAL[nomor_soal]
    jawaban_ronde = {}

    with lock:
        for conn in clients:
            clients[conn]["sudah_jawab"] = False

    paket = {
        "nomor": nomor_soal + 1,
        "total": len(BANK_SOAL),
        "soal": soal_sekarang["soal"],
        "pilihan": soal_sekarang["pilihan"],
        "waktu": WAKTU_JAWAB
    }
    broadcast_semua("SOAL", paket)
    print(f"[SERVER] Soal #{nomor_soal+1} dikirim")

    # Timer countdown
    def hitung_mundur():
        for sisa in range(WAKTU_JAWAB, 0, -1):
            time.sleep(1)
            broadcast_semua("TIMER", {"sisa": sisa - 1})

            with lock:
                semua_jawab = all(clients[c]["sudah_jawab"] for c in clients)
            if semua_jawab:
                break

        evaluasi_jawaban()

    threading.Thread(target=hitung_mundur, daemon=True).start()


def evaluasi_jawaban():
    global nomor_soal

    jawaban_benar = soal_sekarang["jawaban"]
    hasil = {}

    with lock:
        for conn, info in clients.items():
            jwb = jawaban_ronde.get(conn, None)
            benar = jwb == jawaban_benar if jwb else False
            if benar:
                clients[conn]["skor"] += 10
            hasil[info["nama"]] = {
                "jawaban": jwb if jwb else "Tidak menjawab",
                "benar": benar,
                "skor": clients[conn]["skor"]
            }

    broadcast_semua("HASIL_RONDE", {
        "jawaban_benar": jawaban_benar,
        "hasil": hasil
    })

    nomor_soal += 1
    time.sleep(3)

    if nomor_soal < len(BANK_SOAL):
        kirim_soal()
    else:
        selesai_game()


def selesai_game():
    global game_berjalan

    with lock:
        papan_skor = sorted(
            [{"nama": info["nama"], "skor": info["skor"]}
             for conn, info in clients.items()],
            key=lambda x: x["skor"],
            reverse=True
        )

    broadcast_semua("GAME_SELESAI", {"papan_skor": papan_skor})
    game_berjalan = False
    print("[SERVER] Game selesai!")


def mulai_game():
    global game_berjalan, nomor_soal
    game_berjalan = True
    nomor_soal = 0

    # Acak urutan soal
    random.shuffle(BANK_SOAL)

    with lock:
        for conn in clients:
            clients[conn]["skor"] = 0

    print(f"[SERVER] Game dimulai dengan {len(clients)} pemain")
    broadcast_semua("GAME_MULAI", {"pesan": "Game dimulai! Bersiaplah..."})
    time.sleep(2)
    kirim_soal()

# ─── HANDLER CLIENT ───────────────────────────────────────────────────────────
def handle_client(conn, addr):
    global game_berjalan
    print(f"[SERVER] Koneksi baru: {addr}")
    nama_pemain = None

    try:
        buffer = ""
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break

            buffer += data
            while "\n" in buffer:
                baris, buffer = buffer.split("\n", 1)
                if not baris.strip():
                    continue

                try:
                    pesan = json.loads(baris)
                except json.JSONDecodeError:
                    continue

                tipe = pesan.get("tipe")
                isi = pesan.get("data", {})

                # ── BERGABUNG ──
                if tipe == "GABUNG":
                    nama_pemain = isi.get("nama", f"Pemain_{addr[1]}")
                    with lock:
                        if len(clients) >= MAX_PLAYERS:
                            kirim(conn, "ERROR", {"pesan": "Server penuh!"})
                            conn.close()
                            return
                        clients[conn] = {"nama": nama_pemain, "skor": 0, "sudah_jawab": False}

                    kirim(conn, "GABUNG_OK", {"nama": nama_pemain,
                                               "pesan": f"Selamat datang, {nama_pemain}!"})
                    broadcast("INFO", {"pesan": f"🟢 {nama_pemain} bergabung! ({len(clients)}/{MAX_PLAYERS} pemain)"}, kecuali=conn)
                    print(f"[SERVER] {nama_pemain} bergabung ({len(clients)} pemain)")

                    # Kirim daftar pemain saat ini
                    with lock:
                        daftar = [info["nama"] for info in clients.values()]
                    broadcast_semua("PEMAIN_LIST", {"pemain": daftar})

                # ── MULAI GAME (host) ──
                elif tipe == "MULAI":
                    if not game_berjalan:
                        if len(clients) >= 1:
                            threading.Thread(target=mulai_game, daemon=True).start()
                        else:
                            kirim(conn, "ERROR", {"pesan": "Butuh minimal 1 pemain!"})

                # ── JAWABAN ──
                elif tipe == "JAWAB":
                    if game_berjalan and soal_sekarang:
                        with lock:
                            if conn in clients and not clients[conn]["sudah_jawab"]:
                                clients[conn]["sudah_jawab"] = True
                                jawaban_ronde[conn] = isi.get("jawaban", "").upper()
                                nama = clients[conn]["nama"]
                        print(f"[SERVER] {nama} menjawab: {isi.get('jawaban')}")
                        kirim(conn, "JAWAB_OK", {"pesan": "Jawaban diterima!"})

                # ── CHAT ──
                elif tipe == "CHAT":
                    if nama_pemain:
                        broadcast_semua("CHAT", {
                            "dari": nama_pemain,
                            "pesan": isi.get("pesan", "")
                        })

    except Exception as e:
        print(f"[SERVER] Error dari {addr}: {e}")
    finally:
        with lock:
            if conn in clients:
                nama = clients[conn]["nama"]
                del clients[conn]
                print(f"[SERVER] {nama} keluar")
                daftar = [info["nama"] for info in clients.values()]
        broadcast_semua("PEMAIN_LIST", {"pemain": daftar})
        conn.close()

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(MAX_PLAYERS)

    print("=" * 50)
    print("   TRIVIA QUIZ SERVER - Komunikasi Data 2026")
    print("=" * 50)
    print(f"[SERVER] Mendengarkan di {HOST}:{PORT}")
    print(f"[SERVER] Maks pemain: {MAX_PLAYERS}")
    print(f"[SERVER] Jumlah soal: {len(BANK_SOAL)}")
    print("[SERVER] Menunggu pemain bergabung...")

    while True:
        conn, addr = server.accept()
        t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        t.start()

if __name__ == "__main__":
    main()
