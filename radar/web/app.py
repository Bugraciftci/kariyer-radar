import os
from pathlib import Path
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from radar.storage import JobStorage
from radar.engine import JobAggregator
from radar.models import JobPosting

app = FastAPI(title="KariyerRadar API", version="1.0.0")
storage = JobStorage()
aggregator = JobAggregator(storage=storage)

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
INDEX_HTML = (TEMPLATE_DIR / "index.html").read_text(encoding="utf-8")


class AddTargetRequest(BaseModel):
    keyword: str
    sector: str = "other"


@app.get("/", response_class=HTMLResponse)
def index_view():
    return HTMLResponse(content=INDEX_HTML)


@app.get("/api/jobs", response_model=List[Dict[str, Any]])
def list_jobs(
    sector: Optional[str] = Query(None),
    company: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    only_new: bool = Query(False),
    limit: int = Query(150),
    offset: int = Query(0)
):
    jobs = storage.get_jobs(
        sector=sector,
        company=company,
        search=search,
        only_new=only_new,
        limit=limit,
        offset=offset
    )
    return [j.to_dict() for j in jobs]


@app.get("/api/jobs/{job_id}", response_model=Dict[str, Any])
def get_job_detail(job_id: str):
    job = storage.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="İlan bulunamadı.")
    return job.to_dict()


@app.get("/api/stats")
def get_stats():
    return storage.get_stats()


@app.post("/api/scan")
def trigger_scan():
    result = aggregator.run_all()
    return result


@app.post("/api/add-target")
def add_target(req: AddTargetRequest):
    new_jobs = aggregator.scan_single_target(req.keyword, req.sector)
    return {
        "status": "success",
        "keyword": req.keyword,
        "sector": req.sector,
        "discovered_jobs": len(new_jobs)
    }


@app.post("/api/mark-read")
def mark_read():
    storage.mark_all_as_read()
    return {"status": "success"}
