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

Examples:
```
/hospitals?state=Andhra%20Pradesh&district=Srikakulam&limit=25
/hospitals?q=government%20hospital&state=Andhra%20Pradesh
```

## Dataset required

The CSV must contain these 18 columns:
`id, name, facility_type, facility_category, ownership, state, district, taluka, locality, street, pincode, latitude, longitude, phone, email, website, open_24x7, specialties`

The three unused columns `tier_level`, `phone_type`, and `phone_shared` are not imported.

For local use, place the cleaned CSV beside `build_db.py` and name it `sarva_setu_hospitals_app.csv`, then run:

```bash
pip install -r requirements.txt
python build_db.py
uvicorn main:app --reload
```

## Deploy on Render

1. Push this repository to GitHub.
2. In Render, create a new Blueprint and select this repository.
3. When Render asks for `HOSPITAL_CSV_URL`, provide a direct-download URL to the cleaned CSV file. The URL must be reachable by Render without signing in.
4. Deploy. The build step downloads the CSV and creates `hospitals.db`.
5. Open the deployed service URL, then `/docs` to test the API.

Do not put patient records or private medical information in this directory. This API is only a facility directory. Verify contact details and operating status before relying on them. The free Render service may sleep when idle; use an appropriate paid plan for production reliability. Restrict `CORS_ORIGINS` to the required app/web origins before production.
