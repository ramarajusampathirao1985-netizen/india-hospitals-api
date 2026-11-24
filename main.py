import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DB_PATH", str(BASE_DIR / "hospitals.db")))

app = FastAPI(
    title="Sarva Setu – Divyaang Disha Hospital API",
    description="Search and retrieve hospital and healthcare-facility directory records across India.",
    version="1.0.0",
)

# For initial testing only. Restrict this to your Android app/web origins before production.
allowed_origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "*").split(",") if x.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allowed_origins == ["*"] else allowed_origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

@contextmanager
def get_db():
    if not DB_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail="Hospital database is not ready. Configure HOSPITAL_CSV_URL and redeploy.",
        )
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def row_to_dict(row):
    return dict(row) if row is not None else None

@app.get("/")
def root():
    return {
        "service": "Sarva Setu – Divyaang Disha Hospital API",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }

@app.get("/health")
def health():
    if not DB_PATH.exists():
        return {"status": "starting", "database": "not_found"}
    try:
        with get_db() as conn:
            count = conn.execute("SELECT COUNT(*) FROM hospitals").fetchone()[0]
        return {"status": "ok", "database": "ready", "hospital_records": count}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database check failed: {exc}")

@app.get("/hospitals")
def search_hospitals(
    q: Optional[str] = Query(default=None, description="Search hospital name, locality, street or specialties"),
    state: Optional[str] = None,
    district: Optional[str] = None,
    facility_type: Optional[str] = None,
    ownership: Optional[str] = None,
    pincode: Optional[str] = None,
    open_24x7: Optional[bool] = None,
    limit: int = Query(default=25, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    clauses = []
    params = []
    if q and q.strip():
        term = f"%{q.strip()}%"
        clauses.append("(name LIKE ? OR locality LIKE ? OR street LIKE ? OR specialties LIKE ?)")
        params.extend([term, term, term, term])
    for column, value in (
        ("state", state), ("district", district),
        ("facility_type", facility_type), ("ownership", ownership),
        ("pincode", pincode),
    ):
        if value and value.strip():
            clauses.append(f"LOWER({column}) = LOWER(?)")
            params.append(value.strip())
    if open_24x7 is not None:
        clauses.append("LOWER(open_24x7) IN (?, ?)")
        params.extend(["true", "yes"] if open_24x7 else ["false", "no"])
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM hospitals" + where, params).fetchone()[0]
        rows = conn.execute(
            "SELECT id, name, facility_type, facility_category, ownership, state, district, "
            "taluka, locality, street, pincode, latitude, longitude, phone, email, website, "
            "open_24x7, specialties FROM hospitals" + where +
            " ORDER BY name COLLATE NOCASE LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "results": [row_to_dict(row) for row in rows],
    }

@app.get("/hospitals/{hospital_id}")
def get_hospital(hospital_id: str):
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, name, facility_type, facility_category, ownership, state, district, "
            "taluka, locality, street, pincode, latitude, longitude, phone, email, website, "
            "open_24x7, specialties FROM hospitals WHERE id = ? LIMIT 1",
            (hospital_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return row_to_dict(row)

@app.get("/states")
def list_states():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT state FROM hospitals WHERE state IS NOT NULL AND TRIM(state) != '' "
            "ORDER BY state COLLATE NOCASE"
        ).fetchall()
    return {"results": [r["state"] for r in rows]}

@app.get("/districts")
def list_districts(state: str = Query(..., min_length=1)):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT district FROM hospitals WHERE LOWER(state) = LOWER(?) "
            "AND district IS NOT NULL AND TRIM(district) != '' ORDER BY district COLLATE NOCASE",
            (state.strip(),),
        ).fetchall()
    return {"state": state, "results": [r["district"] for r in rows]}
