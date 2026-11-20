import requests
from typing import List
from radar.models import JobPosting
from radar.adapters.base import BaseJobAdapter
from radar.config import DEFAULT_HEADERS


class BaykarPortalAdapter(BaseJobAdapter):
    name = "Baykar Kariyer Portalı"
    sector = "defense"
    api_url = "https://kariyer.baykartech.com/tr/basvuru/serializerProgram/"
    base_web = "https://kariyer.baykartech.com"

    def fetch_jobs(self) -> List[JobPosting]:
        jobs: List[JobPosting] = []

        # Tüm aktif pozisyon sayfalarını çekelim
        page = 1
        while page <= 35:
            try:
                url = f"{self.api_url}?page={page}"
                res = requests.get(url, headers=DEFAULT_HEADERS, timeout=10)
                if res.status_code != 200:
                    break

                data = res.json()
                results = data.get("results", [])
                if not results:
                    break

                for item in results:
                    try:
                        job_id = item.get("id")
                        title = item.get("text", "")
                        category_info = item.get("category", {})
                        category_name = category_info.get("text", "Mühendislik & Operasyon") if isinstance(category_info, dict) else "Savunma"

                        type_info = item.get("type", {})
                        work_model = type_info.get("text", "Tam Zamanlı") if isinstance(type_info, dict) else "Tam Zamanlı"

                        slug = item.get("slug", "")
                        apply_url = f"{self.base_web}{slug}" if slug.startswith("/") else f"{self.base_web}/tr/basvuru/acik-pozisyonlar/"

                        posting = JobPosting(
                            id=f"baykar-{job_id}",
                            company="Baykar Technologies",
                            sector="defense",
                            title=title,
                            location="İstanbul (Özdemir Bayraktar Milli Teknoloji Merkezi)",
                            work_model=work_model,
                            experience_level="Mühendis / Uzman",
                            description_text=f"Baykar bünyesinde {category_name} departmanında açılan {title} pozisyonu. Detaylı bilgi ve doğrudan başvuru için Baykar resmi kariyer portalını ziyaret edin.",
                            apply_url=apply_url,
                            source="baykar_portal"
                        )
                        jobs.append(posting)
                    except Exception:
                        continue

                if not data.get("next"):
                    break
                page += 1
            except Exception as e:
                print(f"[BaykarPortalAdapter] Hata: {e}")
                break

        return jobs
