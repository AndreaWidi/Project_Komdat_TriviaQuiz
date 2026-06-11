"""
TRIVIA QUIZ MULTIPLAYER - CLIENT CLI
Komunikasi Data 2026
TCP Client menggunakan Python socket
"""

import socket
import threading
import json
import sys
import os
import time

# ─── KONFIGURASI ──────────────────────────────────────────────────────────────
SERVER_HOST = '172.20.10.2'
SERVER_PORT = 5555

# ─── WARNA TERMINAL (ANSI) ────────────────────────────────────────────────────
HIJAU   = "\033[92m"
MERAH   = "\033[91m"
KUNING  = "\033[93m"
BIRU    = "\033[94m"
CYAN    = "\033[96m"
BOLD    = "\033[1m"
RESET   = "\033[0m"

def bersih():
    os.system('cls' if os.name == 'nt' else 'clear')

def cetak_header():
    print(f"{CYAN}{BOLD}")
    print("╔══════════════════════════════════════════════╗")
    print("║       🎯 TRIVIA QUIZ MULTIPLAYER 🎯          ║")
    print("║         Komunikasi Data 2026                 ║")
    print("╚══════════════════════════════════════════════╝")
    print(RESET)

# ─── STATE CLIENT ─────────────────────────────────────────────────────────────
nama_saya = ""
soal_aktif = None
sudah_jawab = False
skor_saya = 0
pemain_list = []
game_aktif = False

# ─── FUNGSI KIRIM ─────────────────────────────────────────────────────────────
def kirim(sock, tipe, data={}):
    pesan = json.dumps({"tipe": tipe, "data": data}) + "\n"
    sock.sendall(pesan.encode())

# ─── HANDLER PESAN MASUK ──────────────────────────────────────────────────────
def terima_pesan(sock):
    global soal_aktif, sudah_jawab, skor_saya, pemain_list, game_aktif

    buffer = ""
    try:
        while True:
            data = sock.recv(4096).decode()
            if not data:
                print(f"\n{MERAH}[!] Koneksi ke server terputus.{RESET}")
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

                tipe = pesan["tipe"]
                isi = pesan["data"]

                # ── BERHASIL BERGABUNG ──
                if tipe == "GABUNG_OK":
                    print(f"\n{HIJAU}✅ {isi['pesan']}{RESET}")

                # ── INFO UMUM ──
                elif tipe == "INFO":
                    print(f"\n{KUNING}ℹ  {isi['pesan']}{RESET}")

                # ── DAFTAR PEMAIN ──
                elif tipe == "PEMAIN_LIST":
                    pemain_list = isi["pemain"]
                    print(f"\n{BIRU}👥 Pemain dalam lobby: {', '.join(pemain_list)}{RESET}")
                    if not game_aktif:
                        print(f"{KUNING}   Ketik 'mulai' untuk memulai game / tunggu host memulai{RESET}")

                # ── GAME DIMULAI ──
                elif tipe == "GAME_MULAI":
                    game_aktif = True
                    print(f"\n{HIJAU}{BOLD}🚀 {isi['pesan']}{RESET}")

                # ── SOAL ──
                elif tipe == "SOAL":
                    soal_aktif = isi
                    sudah_jawab = False
                    print(f"\n{CYAN}{'─'*50}{RESET}")
                    print(f"{BOLD}📝 Soal {isi['nomor']}/{isi['total']}{RESET}")
                    print(f"\n{BOLD}{isi['soal']}{RESET}\n")
                    for p in isi["pilihan"]:
                        print(f"   {p}")
                    print(f"\n{KUNING}⏱  Waktu: {isi['waktu']} detik{RESET}")
                    print(f"{CYAN}➤  Jawab dengan ketik A / B / C / D{RESET}")

                # ── TIMER ──
                elif tipe == "TIMER":
                    sisa = isi["sisa"]
                    if sisa <= 5 and sisa > 0 and not sudah_jawab:
                        print(f"{MERAH}⏰ Sisa waktu: {sisa} detik!{RESET}", end="\r")

                # ── KONFIRMASI JAWABAN ──
                elif tipe == "JAWAB_OK":
                    sudah_jawab = True
                    print(f"\n{HIJAU}✔  {isi['pesan']}{RESET}")

                # ── HASIL RONDE ──
                elif tipe == "HASIL_RONDE":
                    print(f"\n{KUNING}{'═'*50}{RESET}")
                    print(f"{BOLD}✅ Jawaban benar: {HIJAU}{isi['jawaban_benar']}{RESET}")
                    print(f"\n{BOLD}📊 Hasil Ronde:{RESET}")
                    for nama, info in isi["hasil"].items():
                        ikon = "✅" if info["benar"] else "❌"
                        warna = HIJAU if info["benar"] else MERAH
                        highlight = BOLD if nama == nama_saya else ""
                        print(f"   {ikon} {highlight}{nama:<15}{RESET} | "
                              f"Jawab: {warna}{info['jawaban']:<20}{RESET} | "
                              f"Skor: {BOLD}{info['skor']}{RESET}")
                        if nama == nama_saya:
                            skor_saya = info["skor"]
                    print(f"\n{CYAN}Soal berikutnya dalam 3 detik...{RESET}")

                # ── GAME SELESAI ──
                elif tipe == "GAME_SELESAI":
                    game_aktif = False
                    soal_aktif = None
                    print(f"\n{CYAN}{'═'*50}")
                    print(f"         🏆 GAME SELESAI! 🏆")
                    print(f"{'═'*50}{RESET}")
                    print(f"\n{BOLD}📋 PAPAN SKOR AKHIR:{RESET}\n")
                    for i, p in enumerate(isi["papan_skor"], 1):
                        medali = ["🥇", "🥈", "🥉"]
                        ikon = medali[i-1] if i <= 3 else f"#{i}"
                        highlight = BOLD if p["nama"] == nama_saya else ""
                        print(f"   {ikon}  {highlight}{p['nama']:<20}{RESET}  {KUNING}{p['skor']} poin{RESET}")
                    print(f"\n{CYAN}Terima kasih telah bermain!{RESET}\n")

                # ── CHAT ──
                elif tipe == "CHAT":
                    print(f"\n{BIRU}💬 {isi['dari']}: {isi['pesan']}{RESET}")

                # ── ERROR ──
                elif tipe == "ERROR":
                    print(f"\n{MERAH}❌ Error: {isi['pesan']}{RESET}")

    except Exception as e:
        print(f"\n{MERAH}[!] Koneksi terputus: {e}{RESET}")
    finally:
        sock.close()
        sys.exit(0)

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    global nama_saya, sudah_jawab, soal_aktif

    bersih()
    cetak_header()

    # Input nama
    nama_saya = input(f"{BOLD}Masukkan nama pemain: {RESET}").strip()
    if not nama_saya:
        nama_saya = "Pemain"

    # Koneksi ke server
    print(f"\n{KUNING}🔌 Menghubungkan ke server {SERVER_HOST}:{SERVER_PORT}...{RESET}")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SERVER_HOST, SERVER_PORT))
        print(f"{HIJAU}✅ Terhubung!{RESET}\n")
    except ConnectionRefusedError:
        print(f"{MERAH}❌ Gagal terhubung. Pastikan server sudah berjalan!{RESET}")
        sys.exit(1)

    # Kirim data bergabung
    kirim(sock, "GABUNG", {"nama": nama_saya})

    # Thread untuk menerima pesan
    t = threading.Thread(target=terima_pesan, args=(sock,), daemon=True)
    t.start()

    # Tampilkan instruksi
    print(f"{KUNING}{'─'*50}")
    print(f"  Perintah yang tersedia:")
    print(f"  mulai  → Mulai game")
    print(f"  A/B/C/D → Jawab soal")
    print(f"  chat <pesan> → Kirim pesan ke semua")
    print(f"  keluar → Keluar dari game")
    print(f"{'─'*50}{RESET}\n")

    # Loop input
    while True:
        try:
            inp = input().strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not inp:
            continue

        inp_lower = inp.lower()

        if inp_lower == "keluar":
            print(f"{KUNING}Sampai jumpa!{RESET}")
            sock.close()
            break

        elif inp_lower == "mulai":
            kirim(sock, "MULAI", {})

        elif inp_lower in ["a", "b", "c", "d"]:
            if soal_aktif and not sudah_jawab:
                kirim(sock, "JAWAB", {"jawaban": inp_lower.upper()})
            elif sudah_jawab:
                print(f"{KUNING}Sudah menjawab, tunggu soal berikutnya.{RESET}")
            else:
                print(f"{KUNING}Belum ada soal aktif.{RESET}")

        elif inp_lower.startswith("chat "):
            pesan = inp[5:].strip()
            if pesan:
                kirim(sock, "CHAT", {"pesan": pesan})

        else:
            print(f"{MERAH}Perintah tidak dikenal. Gunakan: mulai | A/B/C/D | chat <pesan> | keluar{RESET}")

if __name__ == "__main__":
    main()
