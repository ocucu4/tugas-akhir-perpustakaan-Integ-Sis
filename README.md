# Tugas Akhir - REST API Perpustakaan

REST API untuk data buku perpustakaan, dibangun dengan Flask + SQLite,
mengikuti pola Praktikum 5 (validasi, API key, pagination).

## 1. Instalasi

```bash
cd tugas-akhir-perpustakaan
python -m venv venv          # opsional
venv\Scripts\activate        # Windows, lewati kalau tidak pakai venv
pip install -r requirements.txt
```

## 2. Menjalankan

| File | Fungsi | Cara menjalankan |
| --- | --- | --- |
| `app.py` | Server REST API (data di SQLite, `perpus.db`) | `python app.py` |
| `client.py` | Uji semua endpoint lewat HTTP | Terminal 1: `python app.py`, Terminal 2: `python client.py` |

Data tersimpan di `perpus.db`, dibuat otomatis saat `app.py` pertama kali dijalankan
(berisi 3 buku contoh). Hapus file itu untuk mengembalikan data awal.

## 3. Endpoint

Base URL: `http://127.0.0.1:5000/api/buku`

| Metode | Endpoint | Fungsi | Butuh API key? |
| --- | --- | --- | --- |
| GET | `/api/buku` | Semua data (`?page=&limit=&sort=&order=&kategori=&stok_min=`) | Tidak |
| GET | `/api/buku/<id>` | Satu data | Tidak |
| POST | `/api/buku` | Tambah buku (409 kalau isbn sudah ada) | Ya |
| PUT | `/api/buku/<id>` | Ganti seluruh data | Ya |
| PATCH | `/api/buku/<id>` | Ubah sebagian data | Ya |
| DELETE | `/api/buku/<id>` | Hapus buku (balas pesan sukses) | Ya |

Header API key: `X-API-Key: rahasia123` (bisa diganti lewat environment variable `API_KEY`).

`sort` boleh diisi `id`/`isbn`/`judul`/`pengarang`/`kategori`/`stok`, `order` boleh `asc`/`desc`.

Respons DELETE yang berhasil (status 200):

```json
{ "status": "success", "message": "Buku berhasil dihapus" }
```

## 4. Field data buku

| Field | Tipe | Keterangan |
| --- | --- | --- |
| `id` | integer | dibuat otomatis |
| `isbn` | string | wajib, unik, minimal 10 karakter |
| `judul` | string | wajib |
| `pengarang` | string | wajib |
| `kategori` | string | wajib, mis. Fiksi / Non-Fiksi / Komik |
| `stok` | integer | wajib, tidak boleh negatif |

## 5. Contoh curl

```bash
curl http://127.0.0.1:5000/api/buku
curl "http://127.0.0.1:5000/api/buku?kategori=Fiksi&stok_min=3"
curl -X POST http://127.0.0.1:5000/api/buku -H "Content-Type: application/json" -H "X-API-Key: rahasia123" \
  -d "{\"isbn\":\"9786020812345\",\"judul\":\"Negeri 5 Menara\",\"pengarang\":\"Ahmad Fuadi\",\"kategori\":\"Fiksi\",\"stok\":4}"
curl -X PATCH http://127.0.0.1:5000/api/buku/1 -H "Content-Type: application/json" -H "X-API-Key: rahasia123" \
  -d "{\"stok\":10}"
curl -X DELETE http://127.0.0.1:5000/api/buku/1 -H "X-API-Key: rahasia123"
```

## 6. Masalah umum

- `Server belum berjalan` -> jalankan `python app.py` di terminal lain.
- Port 5000 terpakai -> ubah `port=5000` menjadi `port=5001` di `app.py` dan `BASE_URL` di `client.py`.
- `ModuleNotFoundError` -> `pip install -r requirements.txt` belum dijalankan.