from datetime import datetime
from fastapi import FastAPI, Header, HTTPException, Query

app = FastAPI(title="Mock LinkedIn Agent Source API")

DATA = [
    {"id":"L001","name":"Bhavya Sree","job_title":"HR Recruiter","company":"Example Corp","status":"connected","updated_at":"2026-08-22T09:00:00+00:00"},
    {"id":"L002","name":"Vrushali Khedkar","job_title":"Talent Sourcer","company":"Example Tech","status":"connected","updated_at":"2026-08-22T09:05:00+00:00"},
    {"id":"L003","name":"Monali Raut","job_title":"Recruiter","company":"Example Cloud","status":"connected","updated_at":"2026-08-22T09:10:00+00:00"},
    {"id":"L004","name":"Nikita Tiwari","job_title":"Talent Acquisition","company":"Example Services","status":"connected","updated_at":"2026-08-22T09:15:00+00:00"},
    {"id":"L005","name":"Akshaya Mekala","job_title":"HR Recruiter","company":"Example Digital","status":"connected","updated_at":"2026-08-22T09:20:00+00:00"}
]

@app.get("/api/leads")
def get_leads(
    updated_since: str | None = Query(default=None),
    limit: int = Query(default=100, le=1000),
    authorization: str | None = Header(default=None)
):
    if authorization != "Bearer change-me":
        raise HTTPException(status_code=401, detail="Unauthorized")

    rows = DATA
    if updated_since:
        try:
            watermark = datetime.fromisoformat(updated_since)
            rows = [r for r in rows if datetime.fromisoformat(r["updated_at"]) > watermark]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid updated_since")

    return {"data": rows[:limit], "count": min(len(rows), limit)}
