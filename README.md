Anggota Kelompok:
Andrea Widi 2408107010083
Khalisha Ufairah 2408107010084
Zanna Zikraana 2408107010094

# 🎯 Trivia Quiz Multiplayer TCP/UDP
**Proyek Komunikasi Data 2026**

---

## Arsitektur Sistem

```
[Client CLI]  ──TCP──┐
[Client CLI]  ──TCP──┼──> [Server (server.py)]
[Browser]     ──WS──> [Web Bridge (web_client.py)] ──TCP──┘
```

---

## Cara Menjalankan

### 1. Install dependensi
```bash
pip install flask flask-socketio
```

### 2. Jalankan Server (Terminal 1)
```bash
cd server
python server.py
```

### 3. Jalankan Client CLI (Terminal 2, 3, dst)
```bash
cd client
python client.py
```

### 4. Jalankan Web Bridge (opsional, untuk client browser)
```bash
cd web
python web_client.py
# Buka http://localhost:8080
```

---

## Perintah CLI

| Perintah | Keterangan |
|---|---|
| `mulai` | Mulai game (siapa saja bisa) |
| `A` / `B` / `C` / `D` | Jawab soal |
| `chat <pesan>` | Kirim chat ke semua |
| `keluar` | Keluar dari game |

---

## Protokol Komunikasi (TCP, Format JSON)

### Client → Server
```json
{"tipe": "GABUNG",  "data": {"nama": "Budi"}}
{"tipe": "MULAI",   "data": {}}
{"tipe": "JAWAB",   "data": {"jawaban": "B"}}
{"tipe": "CHAT",    "data": {"pesan": "halo!"}}
```

### Server → Client
```json
{"tipe": "GABUNG_OK",    "data": {"nama": "Budi", "pesan": "..."}}
{"tipe": "PEMAIN_LIST",  "data": {"pemain": ["Budi", "Ani"]}}
{"tipe": "GAME_MULAI",   "data": {"pesan": "..."}}
{"tipe": "SOAL",         "data": {"nomor":1, "total":10, "soal":"...", "pilihan":[...], "waktu":15}}
{"tipe": "TIMER",        "data": {"sisa": 10}}
{"tipe": "JAWAB_OK",     "data": {"pesan": "Jawaban diterima!"}}
{"tipe": "HASIL_RONDE",  "data": {"jawaban_benar":"B", "hasil":{...}}}
{"tipe": "GAME_SELESAI", "data": {"papan_skor": [...]}}
{"tipe": "CHAT",         "data": {"dari": "Budi", "pesan": "halo!"}}
```

---

## Fitur
- ✅ Multi-client (hingga 4 pemain bersamaan)
- ✅ Timer 15 detik per soal
- ✅ Skor real-time
- ✅ Chat antar pemain
- ✅ Client CLI (Terminal)
- ✅ Client Web (Browser)
- ✅ 10 soal bank soal Komunikasi Data
