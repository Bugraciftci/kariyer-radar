import requests
from typing import List
from radar.models import JobPosting
from radar.adapters.base import BaseJobAdapter
from radar.config import DEFAULT_HEADERS


class CorporateAtsAdapter(BaseJobAdapter):
    name = "Direct Corporate ATS (Lever & Greenhouse)"
    sector = "tech"

    TARGET_LEVER = [
        {"slug": "getmidas", "company": "Midas", "sector": "fintech"},
        {"slug": "commencis", "company": "Commencis", "sector": "tech"},
        {"slug": "loopgames", "company": "Loop Games", "sector": "gaming"},
        {"slug": "getir", "company": "Getir", "sector": "tech"}
    ]

    TARGET_GREENHOUSE = [
        {"board": "dreamgames", "company": "Dream Games", "sector": "gaming"}
    ]

    def fetch_jobs(self) -> List[JobPosting]:
        jobs: List[JobPosting] = []

        # 1. Lever Endpoints
        for target in self.TARGET_LEVER:
            try:
                url = f"https://api.lever.co/v0/postings/{target['slug']}?mode=json"
                res = requests.get(url, headers=DEFAULT_HEADERS, timeout=10)
                if res.status_code == 200:
                    for item in res.json():
                        job_id = item.get("id")
                        title = item.get("text", "")
                        apply_url = item.get("hostedUrl", "")
                        categories = item.get("categories", {})
                        location = categories.get("location", "İstanbul")
                        commitment = categories.get("commitment", "Tam Zamanlı")
                        desc = item.get("descriptionPlain", "")

                        jobs.append(JobPosting(
                            id=f"{target['slug']}-{job_id}",
                            company=target["company"],
                            sector=target["sector"],
                            title=title,
                            location=location,
                            work_model=commitment,
                            description_text=desc[:1000] if desc else f"{target['company']} {title} pozisyonu.",
                            apply_url=apply_url,
                            source="lever_ats"
                        ))
            except Exception as e:
                print(f"[CorporateAtsAdapter] Lever {target['company']} hatası: {e}")

        # 2. Greenhouse Endpoints
        for target in self.TARGET_GREENHOUSE:
            try:
                url = f"https://boards-api.greenhouse.io/v1/boards/{target['board']}/jobs"
                res = requests.get(url, headers=DEFAULT_HEADERS, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    for item in data.get("jobs", []):
                        job_id = item.get("id")
                        title = item.get("title", "")
                        apply_url = item.get("absolute_url", "")
                        location = item.get("location", {}).get("name", "İstanbul")

                        jobs.append(JobPosting(
                            id=f"{target['board']}-{job_id}",
                            company=target["company"],
                            sector=target["sector"],
                            title=title,
                            location=location,
                            work_model="Tam Zamanlı",
                            description_text=f"{target['company']} açık pozisyon: {title}.",
                            apply_url=apply_url,
                            source="greenhouse_ats"
                        ))
            except Exception as e:
                print(f"[CorporateAtsAdapter] Greenhouse {target['company']} hatası: {e}")

        return jobs
