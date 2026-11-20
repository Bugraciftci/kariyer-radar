import requests
from bs4 import BeautifulSoup
from typing import List
from radar.models import JobPosting
from radar.adapters.base import BaseJobAdapter
from radar.config import DEFAULT_HEADERS


class DefensePortalAdapter(BaseJobAdapter):
    name = "Savunma Sanayii Başkanlığı (SavunmaKariyer)"
    sector = "defense"
    api_url = "https://savunmakariyer.com/api/career-core/public/jobs"
    base_portal = "https://savunmakariyer.com"

    def fetch_jobs(self) -> List[JobPosting]:
        jobs: List[JobPosting] = []
        payload = {
            "page": 1,
            "size": 50,
            "sortDirection": "DESC"
        }
        headers = {
            **DEFAULT_HEADERS,
            "Content-Type": "application/json"
        }

        try:
            res = requests.post(self.api_url, json=payload, headers=headers, timeout=12)
            if res.status_code != 200:
                print(f"[DefensePortalAdapter] HTTP {res.status_code}")
                return jobs

            data = res.json()
            content = data.get("data", {}).get("content", [])
            for item in content:
                try:
                    job_id = item.get("id")
                    title = item.get("jobTitle", "Savunma Mühendisi")
                    company = item.get("companyName", "Savunma Sanayii")
                    location = item.get("jobLocation", "Ankara / Türkiye")
                    job_type = item.get("jobType", "FULL_TIME")

                    raw_html = item.get("jobDescription", "")
                    clean_text = ""
                    requirements = []
                    if raw_html:
                        soup = BeautifulSoup(raw_html, "html.parser")
                        clean_text = soup.get_text(separator="\n", strip=True)

                        # Extract bullet points as requirements
                        for li in soup.find_all("li"):
                            txt = li.get_text(strip=True)
                            if len(txt) > 5 and len(requirements) < 8:
                                requirements.append(txt)

                    start_date = item.get("startDate", "")
                    end_date = item.get("endDate", "")

                    apply_url = f"{self.base_portal}/ilanlar/ilanDetay/{job_id}"

                    posting = JobPosting(
                        id=f"defense-{job_id}",
                        company=company,
                        sector="defense",
                        title=title,
                        location=location,
                        work_model="Tam Zamanlı (Yerinde / Güvenlikli Tesis)" if job_type == "FULL_TIME" else job_type,
                        experience_level="Mühendis / Uzman",
                        description_text=clean_text or f"{company} bünyesinde {title} pozisyonu.",
                        requirements=requirements,
                        apply_url=apply_url,
                        posted_date=start_date[:10] if start_date else None,
                        deadline=end_date[:10] if end_date else None,
                        source="savunmakariyer"
                    )
                    jobs.append(posting)
                except Exception:
                    continue
        except Exception as e:
            print(f"[DefensePortalAdapter] Hata: {e}")

        return jobs
