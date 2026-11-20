import requests
from datetime import datetime
from bs4 import BeautifulSoup
from typing import List
from radar.models import JobPosting
from radar.adapters.base import BaseJobAdapter
from radar.config import DEFAULT_HEADERS


class AkbankPortalAdapter(BaseJobAdapter):
    name = "Akbank Kariyer Portalı"
    sector = "bank"
    list_url = "https://api.akbank.com/api/v1/crm/candidateportal/advert/list"
    detail_url = "https://api.akbank.com/api/v1/crm/candidateportal/advert/detail"
    portal_web = "https://kariyer.akbank.com"

    def fetch_jobs(self) -> List[JobPosting]:
        jobs: List[JobPosting] = []
        headers = {
            **DEFAULT_HEADERS,
            "Content-Type": "application/json"
        }

        try:
            res = requests.post(self.list_url, json={}, headers=headers, timeout=12)
            if res.status_code != 200:
                print(f"[AkbankPortalAdapter] List HTTP {res.status_code}")
                return jobs

            data = res.json()
            for item in data:
                try:
                    job_id = item.get("id")
                    title = item.get("title", "Bankacılık Pozisyonu")
                    city = item.get("city", "İstanbul")
                    work_type = item.get("workType", "Tam zamanlı")
                    work_model_str = item.get("workModel", "Hibrit")
                    experience = item.get("experience", "")
                    exp_interval = item.get("experienceInterval", "")
                    exp_full = f"{experience} ({exp_interval})".strip() if experience else exp_interval

                    deadline_ms = item.get("applicationDeadLine")
                    deadline_str = None
                    if deadline_ms:
                        try:
                            deadline_str = datetime.fromtimestamp(deadline_ms / 1000).strftime("%Y-%m-%d")
                        except Exception:
                            pass

                    posted_ms = item.get("createDate")
                    posted_str = None
                    if posted_ms:
                        try:
                            posted_str = datetime.fromtimestamp(posted_ms / 1000).strftime("%Y-%m-%d")
                        except Exception:
                            pass

                    # Detail fetching is done in parallel if needed
                    posting = JobPosting(
                        id=f"akbank-{job_id}",
                        company="Akbank",
                        sector="bank",
                        title=title,
                        location=city,
                        work_model=f"{work_type} / {work_model_str}",
                        experience_level=exp_full or "Deneyimli / Uzman",
                        description_text=f"Akbank {title} - {city} lokasyonunda {work_model_str} çalışma modeli ile açık pozisyon.",
                        requirements=[],
                        apply_url=f"{self.portal_web}/shared/advert-list/{job_id}",
                        posted_date=posted_str,
                        deadline=deadline_str,
                        source="akbank_portal"
                    )
                    jobs.append((posting, job_id))
                except Exception:
                    continue

            # Fetch details in parallel with max_workers=8
            from concurrent.futures import ThreadPoolExecutor

            def _enrich_detail(pair):
                posting, jid = pair
                try:
                    det_res = requests.post(self.detail_url, json={"id": jid}, headers=headers, timeout=5)
                    if det_res.status_code == 200:
                        det = det_res.json()
                        raw_desc = det.get("jobDescription", "")
                        raw_qual = det.get("jobQualifications", "")
                        if raw_desc or raw_qual:
                            soup_d = BeautifulSoup(raw_desc or "", "html.parser")
                            soup_q = BeautifulSoup(raw_qual or "", "html.parser")
                            posting.description_text = f"{soup_d.get_text(separator=' ', strip=True)}\n\nNitelikler:\n{soup_q.get_text(separator=' ', strip=True)}"
                            for li in soup_q.find_all("li"):
                                txt = li.get_text(strip=True)
                                if len(txt) > 5 and len(posting.requirements) < 8:
                                    posting.requirements.append(txt)
                except Exception:
                    pass
                return posting

            final_jobs = []
            with ThreadPoolExecutor(max_workers=8) as executor:
                final_jobs = list(executor.map(_enrich_detail, jobs))

            return final_jobs
        except Exception as e:
            print(f"[AkbankPortalAdapter] Hata: {e}")

        return [p for p, _ in jobs] if isinstance(jobs, list) and jobs and isinstance(jobs[0], tuple) else []
