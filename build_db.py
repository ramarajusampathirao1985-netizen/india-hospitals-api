import csv
import os
import sqlite3
import urllib.request
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = Path(os.getenv("CSV_PATH", str(BASE_DIR / "sarva_setu_hospitals_app.csv")))
DB_PATH = Path(os.getenv("DB_PATH", str(BASE_DIR / "hospitals.db")))
CSV_URL = os.getenv("HOSPITAL_CSV_URL", "").strip()

COLUMNS = [
    "id", "name", "facility_type", "facility_category", "ownership",
    "state", "district", "taluka", "locality", "street", "pincode",
    "latitude", "longitude", "phone", "email", "website", "open_24x7",
    "specialties",
]

def obtain_csv():
    if CSV_URL:
        download_path = BASE_DIR / "hospital_dataset_download"
        print("Downloading hospital dataset from HOSPITAL_CSV_URL ...")
        request = urllib.request.Request(CSV_URL, headers={"User-Agent": "SarvaSetu-HospitalAPI/1.0"})
        with urllib.request.urlopen(request, timeout=240) as response, open(download_path, "wb") as out:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
        if zipfile.is_zipfile(download_path):
            with zipfile.ZipFile(download_path) as archive:
                candidates = [n for n in archive.namelist() if n.lower().endswith(".csv") and not n.startswith("__MACOSX/")]
                if not candidates:
                    raise ValueError("The downloaded ZIP does not contain a CSV file")
                # Use the first CSV file in the dataset archive.
                with archive.open(candidates[0]) as source, open(CSV_PATH, "wb") as target:
                    while True:
                        chunk = source.read(1024 * 1024)
                        if not chunk:
                            break
                        target.write(chunk)
            print(f"Extracted CSV to {CSV_PATH}")
        else:
            download_path.replace(CSV_PATH)
            print(f"Downloaded CSV to {CSV_PATH}")
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"CSV not found: {CSV_PATH}. Set HOSPITAL_CSV_URL to a direct-download URL "
            "for the CSV or ZIP dataset, or place sarva_setu_hospitals_app.csv beside this script."
        )

def clean(value):
    if value is None:
        return ""
    return " ".join(str(value).replace("\\u0000", "").split())

def main():
    obtain_csv()
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE hospitals (
            row_num INTEGER PRIMARY KEY AUTOINCREMENT,
            id TEXT,
            name TEXT,
            facility_type TEXT,
            facility_category TEXT,
            ownership TEXT,
            state TEXT,
            district TEXT,
            taluka TEXT,
            locality TEXT,
            street TEXT,
            pincode TEXT,
            latitude TEXT,
            longitude TEXT,
            phone TEXT,
            email TEXT,
            website TEXT,
            open_24x7 TEXT,
            specialties TEXT
        )
    """)

    placeholders = ",".join(["?"] * len(COLUMNS))
    sql = f"INSERT INTO hospitals ({','.join(COLUMNS)}) VALUES ({placeholders})"
    count = 0
    with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames:
            raise ValueError("CSV has no header row")
        missing = [column for column in COLUMNS if column not in reader.fieldnames]
        if missing:
            raise ValueError(f"CSV is missing required columns: {', '.join(missing)}")
        batch = []
        for record in reader:
            batch.append(tuple(clean(record.get(column, "")) for column in COLUMNS))
            if len(batch) >= 2000:
                conn.executemany(sql, batch)
                count += len(batch)
                batch.clear()
                print(f"Imported {count} records ...")
        if batch:
            conn.executemany(sql, batch)
            count += len(batch)

    conn.executescript("""
        CREATE INDEX idx_hospitals_id ON hospitals(id);
        CREATE INDEX idx_hospitals_name ON hospitals(name);
        CREATE INDEX idx_hospitals_state ON hospitals(state);
        CREATE INDEX idx_hospitals_district ON hospitals(district);
        CREATE INDEX idx_hospitals_type ON hospitals(facility_type);
        CREATE INDEX idx_hospitals_pincode ON hospitals(pincode);
    """)
    conn.commit()
    conn.close()
    print(f"Database created: {DB_PATH}")
    print(f"Imported records: {count}")

if __name__ == "__main__":
    main()
