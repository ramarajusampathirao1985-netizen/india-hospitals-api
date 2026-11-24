# Sarva Setu – Divyaang Disha Hospital API

FastAPI + SQLite backend for searching the India-wide hospital and healthcare-facility directory.

## API endpoints

- `GET /` – service information
- `GET /health` – API and database status
- `GET /hospitals` – search and filter hospitals
- `GET /hospitals/{id}` – fetch one record by hospital ID
- `GET /states` – list available states
- `GET /districts?state=Andhra%20Pradesh` – list districts in a state
- `GET /docs` – interactive Swagger documentation

## Dataset

The prepared dataset contains 231,379 hospital/facility records and 18 columns:

`id, name, facility_type, facility_category, ownership, state, district, taluka, locality, street, pincode, latitude, longitude, phone, email, website, open_24x7, specialties`

The unused columns `tier_level`, `phone_type`, and `phone_shared` are excluded.

The API accepts a direct-download CSV URL or ZIP URL through the `HOSPITAL_CSV_URL` environment variable. For the ZIP prepared for this project, upload `sarva_setu_hospitals_dataset.zip` to the repository root, then set:

```
HOSPITAL_CSV_URL=https://raw.githubusercontent.com/ramarajusampathirao1985-netizen/india-hospitals-api/main/sarva_setu_hospitals_dataset.zip
```

## Local setup

Place `sarva_setu_hospitals_app.csv` beside `build_db.py`, then run:

```bash
pip install -r requirements.txt
python build_db.py
uvicorn main:app --reload
```

## Render deployment

1. Upload `sarva_setu_hospitals_dataset.zip` to the root of this GitHub repository.
2. In Render, create a new Blueprint and select this repository (or deploy the existing Blueprint).
3. Set the `HOSPITAL_CSV_URL` environment variable to the raw ZIP URL shown above.
4. Deploy. The build command downloads the ZIP, extracts the CSV, and creates `hospitals.db`.
5. Open the service URL and visit `/docs` to test the API.

The free Render service may sleep when idle. For production reliability, use an appropriate paid plan and persistent storage or an external database. Restrict `CORS_ORIGINS` to the required app/web origins before production.

This API is a facility directory, not a patient-record system. Verify facility contact details and operating status before relying on them.
