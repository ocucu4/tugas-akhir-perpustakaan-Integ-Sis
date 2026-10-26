"""
Tugas Akhir - REST API Perpustakaan (SQLite, validasi, API key, pagination)
Jalankan: python app.py   ->  http://127.0.0.1:5000/api/buku
API key untuk POST/PUT/PATCH/DELETE: header  X-API-Key: rahasia123
"""
import os
import sqlite3
from functools import wraps

from flask import Flask, g, jsonify, request

app = Flask(__name__)
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "perpus.db")
API_KEY = os.environ.get("API_KEY", "rahasia123")  # bisa diganti lewat environment variable
FIELDS = ["isbn", "judul", "pengarang", "kategori", "stok"]


# ---------- Koneksi database ----------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row  # baris bisa diakses seperti dict
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DATABASE) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS buku (
                id         INTEGER PRIMARY KEY,
                isbn       TEXT UNIQUE NOT NULL,
                judul      TEXT NOT NULL,
                pengarang  TEXT NOT NULL,
                kategori   TEXT NOT NULL,
                stok       INTEGER NOT NULL
            )
        """)
        if db.execute("SELECT COUNT(*) FROM buku").fetchone()[0] == 0:
            db.executemany(
                "INSERT INTO buku (isbn, judul, pengarang, kategori, stok) VALUES (?, ?, ?, ?, ?)",
                [("9786020412123", "Laskar Pelangi", "Andrea Hirata", "Fiksi", 5),
                 ("9786020362556", "Bumi Manusia", "Pramoedya Ananta Toer", "Fiksi", 3),
                 ("9786024246108", "Sapiens", "Yuval Noah Harari", "Non-Fiksi", 2)],
            )


# ---------- Helper ----------
def error(pesan, status):
    return jsonify({"status": "error", "message": pesan}), status


def validasi(data, wajib_semua=True):
    """Kembalikan pesan error, atau None jika valid."""
    if not isinstance(data, dict):
        return "Body harus JSON"
    if wajib_semua:
        kurang = [f for f in FIELDS if f not in data]
        if kurang:
            return f"Field wajib: {', '.join(kurang)}"
    if "isbn" in data and len(str(data["isbn"]).strip()) < 10:
        return "isbn minimal 10 karakter"
    if "judul" in data and len(str(data["judul"]).strip()) < 1:
        return "judul tidak boleh kosong"
    if "pengarang" in data and len(str(data["pengarang"]).strip()) < 1:
        return "pengarang tidak boleh kosong"
    if "kategori" in data and len(str(data["kategori"]).strip()) < 1:
        return "kategori tidak boleh kosong"
    if "stok" in data:
        try:
            stok = int(data["stok"])
        except (TypeError, ValueError):
            return "stok harus angka bulat"
        if stok < 0:
            return "stok tidak boleh negatif"
    return None


def butuh_api_key(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.headers.get("X-API-Key") != API_KEY:
            return error("API key tidak valid atau tidak ada", 401)
        return f(*args, **kwargs)
    return wrapper


SORTABLE = {"id", "isbn", "judul", "pengarang", "kategori", "stok"}


# ---------- Endpoint ----------
# GET semua buku (+ pagination ?page=&limit=, sort ?sort=&order=, filter ?kategori=&stok_min=)
@app.get("/api/buku")
def get_semua():
    page = request.args.get("page", 1, type=int)
    limit = min(request.args.get("limit", 10, type=int), 100)
    if page < 1 or limit < 1:
        return error("page dan limit harus >= 1", 400)
    offset = (page - 1) * limit

    sort = request.args.get("sort", "id")
    order = request.args.get("order", "asc").lower()
    if sort not in SORTABLE:
        return error(f"sort harus salah satu dari: {', '.join(sorted(SORTABLE))}", 400)
    if order not in ("asc", "desc"):
        return error("order harus 'asc' atau 'desc'", 400)

    sql, args = "FROM buku", []
    kategori = request.args.get("kategori")
    if kategori:
        sql += " WHERE LOWER(kategori) = LOWER(?)"
        args.append(kategori)

    stok_min = request.args.get("stok_min", type=int)
    if stok_min is not None:
        sql += (" AND" if "WHERE" in sql else " WHERE") + " stok >= ?"
        args.append(stok_min)

    db = get_db()
    total = db.execute(f"SELECT COUNT(*) {sql}", args).fetchone()[0]
    # nama kolom sort/order berasal dari SORTABLE dan whitelist asc/desc, jadi aman disisipkan langsung
    rows = db.execute(
        f"SELECT * {sql} ORDER BY {sort} {order.upper()} LIMIT ? OFFSET ?", args + [limit, offset]
    ).fetchall()

    return jsonify({
        "status": "success",
        "data": [dict(r) for r in rows],
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit,
        },
    }), 200


# GET satu buku berdasarkan id
@app.get("/api/buku/<int:buku_id>")
def get_satu(buku_id):
    row = get_db().execute("SELECT * FROM buku WHERE id = ?", (buku_id,)).fetchone()
    if row is None:
        return error("Buku tidak ditemukan", 404)
    return jsonify({"status": "success", "data": dict(row)}), 200


# POST tambah buku baru (butuh API key, isbn duplikat -> 409)
@app.post("/api/buku")
@butuh_api_key
def tambah():
    data = request.get_json(silent=True)
    pesan = validasi(data)
    if pesan:
        return error(pesan, 400)
    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO buku (isbn, judul, pengarang, kategori, stok) VALUES (?, ?, ?, ?, ?)",
            (str(data["isbn"]).strip(), data["judul"].strip(), data["pengarang"].strip(),
             data["kategori"].strip(), int(data["stok"])),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return error("isbn sudah terdaftar", 409)
    return get_satu(cur.lastrowid)[0], 201


# PUT ganti seluruh data buku (butuh API key, semua field wajib diisi)
@app.put("/api/buku/<int:buku_id>")
@butuh_api_key
def ganti(buku_id):
    data = request.get_json(silent=True)
    pesan = validasi(data)
    if pesan:
        return error(pesan, 400)
    db = get_db()
    try:
        cur = db.execute(
            "UPDATE buku SET isbn = ?, judul = ?, pengarang = ?, kategori = ?, stok = ? WHERE id = ?",
            (str(data["isbn"]).strip(), data["judul"].strip(), data["pengarang"].strip(),
             data["kategori"].strip(), int(data["stok"]), buku_id),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return error("isbn sudah terdaftar", 409)
    if cur.rowcount == 0:
        return error("Buku tidak ditemukan", 404)
    return get_satu(buku_id)


# PATCH ubah sebagian data buku saja (butuh API key, field lain dibiarkan)
@app.patch("/api/buku/<int:buku_id>")
@butuh_api_key
def ubah(buku_id):
    data = request.get_json(silent=True)
    pesan = validasi(data, wajib_semua=False)
    if pesan:
        return error(pesan, 400)
    kolom = {f: data[f] for f in FIELDS if f in data}
    if not kolom:
        return error("Tidak ada field yang diubah", 400)
    set_sql = ", ".join(f"{k} = ?" for k in kolom)  # nama kolom dari FIELDS, aman
    db = get_db()
    try:
        cur = db.execute(f"UPDATE buku SET {set_sql} WHERE id = ?", [*kolom.values(), buku_id])
        db.commit()
    except sqlite3.IntegrityError:
        return error("isbn sudah terdaftar", 409)
    if cur.rowcount == 0:
        return error("Buku tidak ditemukan", 404)
    return get_satu(buku_id)


# DELETE hapus buku berdasarkan id (butuh API key)
@app.delete("/api/buku/<int:buku_id>")
@butuh_api_key
def hapus(buku_id):
    db = get_db()
    cur = db.execute("DELETE FROM buku WHERE id = ?", (buku_id,))
    db.commit()
    if cur.rowcount == 0:
        return error("Buku tidak ditemukan", 404)
    return jsonify({"status": "success", "message": "Buku berhasil dihapus"}), 200


# Handler untuk endpoint/path yang tidak dikenali
@app.errorhandler(404)
def not_found(e):
    return error("Endpoint tidak ditemukan", 404)


# Handler untuk metode HTTP yang tidak diizinkan di endpoint tersebut
@app.errorhandler(405)
def method_not_allowed(e):
    return error("Metode tidak diizinkan", 405)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)