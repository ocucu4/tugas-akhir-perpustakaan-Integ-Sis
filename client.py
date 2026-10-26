"""
Tugas Akhir - Menguji app.py (REST API Perpustakaan)
Langkah:
  1. Terminal 1: python app.py
  2. Terminal 2: python client.py
"""
import sys

import requests

BASE_URL = "http://127.0.0.1:5000/api/buku"
HEADERS = {"X-API-Key": "rahasia123"}
TIMEOUT = 5
hasil = []


def uji(no, judul, r, status_harapan):
    ok = r.status_code == status_harapan
    hasil.append(ok)
    print(f"\n[{no:>2}] {judul}")
    print(f"     Status : {r.status_code} (harapan {status_harapan}) -> {'LULUS' if ok else 'GAGAL'}")
    print("     Body   :", r.json() if r.content else "(kosong)")
    return r


def main():
    try:
        requests.get(BASE_URL, timeout=TIMEOUT)
    except requests.exceptions.ConnectionError:
        print("Server belum berjalan. Jalankan dulu: python app.py")
        sys.exit(1)

    uji(1, "GET semua (pagination page=1 limit=2)",
        requests.get(BASE_URL, params={"page": 1, "limit": 2}, timeout=TIMEOUT), 200)

    uji(2, "GET filter kategori=Fiksi",
        requests.get(BASE_URL, params={"kategori": "Fiksi"}, timeout=TIMEOUT), 200)

    uji(3, "GET filter stok_min=3",
        requests.get(BASE_URL, params={"stok_min": 3}, timeout=TIMEOUT), 200)

    data = {"isbn": "9786020812345", "judul": "Negeri 5 Menara", "pengarang": "Ahmad Fuadi",
             "kategori": "Fiksi", "stok": 4}

    uji(4, "POST tanpa API key", requests.post(BASE_URL, json=data, timeout=TIMEOUT), 401)

    r = uji(5, "POST dengan API key", requests.post(BASE_URL, json=data, headers=HEADERS, timeout=TIMEOUT), 201)
    new_id = r.json()["data"]["id"]

    uji(6, "POST isbn duplikat", requests.post(BASE_URL, json=data, headers=HEADERS, timeout=TIMEOUT), 409)

    uji(7, "POST isbn tidak valid (terlalu pendek)",
        requests.post(BASE_URL, json={**data, "isbn": "123"}, headers=HEADERS, timeout=TIMEOUT), 400)

    uji(8, "POST stok negatif",
        requests.post(BASE_URL, json={**data, "isbn": "9786020999999", "stok": -1},
                      headers=HEADERS, timeout=TIMEOUT), 400)

    uji(9, "GET satu id baru", requests.get(f"{BASE_URL}/{new_id}", timeout=TIMEOUT), 200)

    uji(10, "PATCH stok jadi 10",
        requests.patch(f"{BASE_URL}/{new_id}", json={"stok": 10}, headers=HEADERS, timeout=TIMEOUT), 200)

    uji(11, "PATCH tanpa field apapun",
        requests.patch(f"{BASE_URL}/{new_id}", json={}, headers=HEADERS, timeout=TIMEOUT), 400)

    uji(12, "PUT id yang tidak ada",
        requests.put(f"{BASE_URL}/9999", json=data, headers=HEADERS, timeout=TIMEOUT), 404)

    uji(13, f"DELETE id {new_id}",
        requests.delete(f"{BASE_URL}/{new_id}", headers=HEADERS, timeout=TIMEOUT), 200)

    uji(14, "DELETE tanpa API key",
        requests.delete(f"{BASE_URL}/1", timeout=TIMEOUT), 401)

    uji(15, "GET page=0 (tidak valid)", requests.get(BASE_URL, params={"page": 0}, timeout=TIMEOUT), 400)

    print("\n" + "=" * 50)
    print(f"Ringkasan: {sum(hasil)}/{len(hasil)} skenario LULUS")


if __name__ == "__main__":
    main()