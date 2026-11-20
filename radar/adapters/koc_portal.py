import requests
from bs4 import BeautifulSoup
from typing import List
from radar.models import JobPosting
from radar.adapters.base import BaseJobAdapter
from radar.config import DEFAULT_HEADERS


class KocPortalAdapter(BaseJobAdapter):
    name = "Koç Topluluğu Kariyerim"
    sector = "koc"
    base_url = "https://www.kockariyerim.com"

    def fetch_jobs(self) -> List[JobPosting]:
        jobs: List[JobPosting] = []
        page = 1
        max_pages = 4  # Koç genellikle 2-4 sayfada ~40-60 ilan listeler

        while page <= max_pages:
            url = f"{self.base_url}/jobAd/list?pageIndex={page}"
            try:
                res = requests.get(url, headers=DEFAULT_HEADERS, timeout=12)
                if res.status_code != 200:
                    break

                soup = BeautifulSoup(res.text, "html.parser")
                boxes = soup.find_all("div", class_="job-box-v3")
                if not boxes:
                    break

                for b in boxes:
                    try:
                        link_tag = b.find("a", href=True)
                        if not link_tag:
                            continue
                        rel_link = link_tag["href"]
                        apply_url = f"{self.base_url}{rel_link}" if rel_link.startswith("/") else rel_link

                        job_id = rel_link.split("/")[-1].split("?")[0]
                        if not job_id:
                            continue

                        # Text tokens: [Title, Company, Location, Detayı Gör]
                        tokens = [t.strip() for t in b.get_text(separator="\n", strip=True).split("\n") if t.strip()]
                        title = tokens[0] if len(tokens) > 0 else "Pozisyon"
                        company = tokens[1] if len(tokens) > 1 else "Koç Topluluğu"
                        location = tokens[2] if len(tokens) > 2 else "Türkiye"

                        if "Detayı Gör" in location:
                            location = "Türkiye"

                        posting = JobPosting(
                            id=f"koc-{job_id}",
                            company=company,
                            sector="koc",
                            title=title,
                            location=location,
                            work_model="Tam Zamanlı / Hibrit",
                            description_text=f"{company} bünyesinde açılan {title} pozisyonu. Detaylar ve başvuru için Koç Kariyerim resmi ilan sayfasını ziyaret edin.",
                            apply_url=apply_url,
                            source="koc_portal"
                        )
                        jobs.append(posting)
                    except Exception:
                        continue

                # Eğer bulunan kutu sayısı sayfa boyutundan azsa sonraki sayfa yoktur
                if len(boxes) < 15:
                    break

                page += 1
            except Exception as e:
                print(f"[KocPortalAdapter] Hata: {e}")
                break

        return jobs
