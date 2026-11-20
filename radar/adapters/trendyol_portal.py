import requests
from typing import List
from radar.models import JobPosting
from radar.adapters.base import BaseJobAdapter
from radar.config import DEFAULT_HEADERS


class TrendyolPortalAdapter(BaseJobAdapter):
    name = "Trendyol Careers"
    sector = "tech"
    api_url = "https://api.lever.co/v0/postings/trendyol?mode=json"

    def fetch_jobs(self) -> List[JobPosting]:
        jobs: List[JobPosting] = []
        try:
            res = requests.get(self.api_url, headers=DEFAULT_HEADERS, timeout=25)
            if res.status_code != 200:
                print(f"[TrendyolPortalAdapter] HTTP {res.status_code}")
                return jobs

            data = res.json()
            for item in data:
                try:
                    job_id = item.get("id")
                    title = item.get("text", "")
                    apply_url = item.get("hostedUrl", "https://careers.trendyol.com")

                    categories = item.get("categories", {})
                    location = categories.get("location", "İstanbul, Maslak")
                    team = categories.get("team", "Technology")
                    commitment = categories.get("commitment", "Full-time")

                    workplace_type = item.get("workplaceType", "hybrid").capitalize()
                    work_model = f"{commitment} ({workplace_type})"

                    desc_plain = item.get("descriptionPlain", "")
                    additional_plain = item.get("additionalPlain", "")
                    full_desc = f"{desc_plain}\n\n{additional_plain}".strip()

                    requirements = []
                    for lst in item.get("lists", []):
                        sub_text = lst.get("text", "")
                        content = lst.get("content", "")
                        if "Looking For" in sub_text or "Qualifications" in sub_text:
                            # Clean bullet items
                            clean_items = [line.strip().lstrip("•-* ") for line in content.split("\n") if line.strip()]
                            requirements.extend(clean_items[:8])

                    posting = JobPosting(
                        id=f"trendyol-{job_id}",
                        company="Trendyol",
                        sector="tech",
                        title=title,
                        location=location,
                        work_model=work_model,
                        experience_level="Deneyimli / Uzman" if "Senior" in title or "Lead" in title else "Genel",
                        description_text=full_desc,
                        requirements=requirements,
                        apply_url=apply_url,
                        source="trendyol_portal"
                    )
                    jobs.append(posting)
                except Exception:
                    continue
        except Exception as e:
            print(f"[TrendyolPortalAdapter] Hata: {e}")

        return jobs
