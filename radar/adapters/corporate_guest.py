import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from radar.models import JobPosting
from radar.adapters.base import BaseJobAdapter
from radar.config import DEFAULT_HEADERS


class CorporateGuestAdapter(BaseJobAdapter):
    """
    Şirketlerin onaylı kurumsal profillerini ve açık pozisyonlarını
    oturum gerektirmeyen misafir motoru üzerinden yüksek hızda tarar.
    """
    name = "Verified Corporate Portals & ATS Engine"
    sector = "other"

    PRESET_TARGETS = [
        # Bankalar
        {"company": "Garanti BBVA", "sector": "bank"},
        {"company": "Yapı Kredi", "sector": "bank"},
        {"company": "QNB Finansbank", "sector": "bank"},
        {"company": "DenizBank", "sector": "bank"},
        {"company": "Papara", "sector": "bank"},

        # Telekomünikasyon
        {"company": "Turkcell", "sector": "telecom"},
        {"company": "Vodafone", "sector": "telecom"},
        {"company": "Türk Telekom", "sector": "telecom"},

        # E-Ticaret & Perakende
        {"company": "Hepsiburada", "sector": "tech"},
        {"company": "Yemeksepeti", "sector": "tech"},
        {"company": "Sahibinden.com", "sector": "tech"},
        {"company": "Boyner", "sector": "cosmetics"},
        {"company": "Mavi", "sector": "cosmetics"},

        # Kozmetik
        {"company": "Watsons Turkey", "sector": "cosmetics"},
        {"company": "Gratis", "sector": "cosmetics"},
        {"company": "Flormar", "sector": "cosmetics"},
        {"company": "Sephora", "sector": "cosmetics"},
        {"company": "L'Oréal", "sector": "cosmetics"},

        # Big 4 & Danışmanlık
        {"company": "PwC Türkiye", "sector": "big4"},
        {"company": "Deloitte", "sector": "big4"},
        {"company": "EY", "sector": "big4"},
        {"company": "KPMG Türkiye", "sector": "big4"},
        {"company": "McKinsey & Company", "sector": "big4"},

        # FMCG & Gıda
        {"company": "Unilever", "sector": "fmcg"},
        {"company": "Procter & Gamble", "sector": "fmcg"},
        {"company": "Coca-Cola İçecek", "sector": "fmcg"},
        {"company": "Nestlé", "sector": "fmcg"},

        # Enerji & Otomotiv
        {"company": "SOCAR Türkiye", "sector": "energy"},
        {"company": "Enerjisa", "sector": "energy"},
        {"company": "TOGG", "sector": "energy"}
    ]

    def __init__(self, custom_targets: List[Dict[str, str]] = None, custom_only: bool = False):
        if custom_only and custom_targets:
            self.targets = []
            for ct in custom_targets:
                self.targets.append({
                    "company": ct.get("keyword", ct.get("company", "")),
                    "sector": ct.get("sector", "other")
                })
        else:
            self.targets = list(self.PRESET_TARGETS)
            if custom_targets:
                for ct in custom_targets:
                    self.targets.append({
                        "company": ct.get("keyword", ct.get("company", "")),
                        "sector": ct.get("sector", "other")
                    })

    def _fetch_company_jobs(self, target: Dict[str, str]) -> List[JobPosting]:
        company_name = target["company"]
        sector = target["sector"]
        company_jobs = []

        url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={requests.utils.quote(company_name)}&location=Turkey"
        try:
            res = requests.get(url, headers=DEFAULT_HEADERS, timeout=10)
            if res.status_code != 200:
                return []

            soup = BeautifulSoup(res.text, "html.parser")
            cards = soup.find_all("div", class_="job-search-card")

            for c in cards[:6]:  # Her şirketten en güncel 6 ilanı al
                try:
                    title_elem = c.find("h3", class_="base-search-card__title")
                    if not title_elem:
                        continue
                    title = title_elem.get_text(strip=True)

                    comp_elem = c.find("h4", class_="base-search-card__subtitle")
                    comp = comp_elem.get_text(strip=True) if comp_elem else company_name

                    loc_elem = c.find("span", class_="job-search-card__location")
                    loc = loc_elem.get_text(strip=True) if loc_elem else "Türkiye"

                    link_elem = c.find("a", class_="base-card__full-link")
                    apply_url = link_elem["href"] if link_elem and link_elem.has_attr("href") else f"https://www.google.com/search?q={company_name}+is+ilanlari"

                    urn = c.get("data-entity-urn", "")
                    job_id_num = urn.split(":")[-1] if ":" in urn else str(hash(title + comp) % 10000000)

                    time_elem = c.find("time")
                    posted_date = time_elem.get("datetime", "") if time_elem else None

                    posting = JobPosting(
                        id=f"corp-{job_id_num}",
                        company=comp,
                        sector=sector,
                        title=title,
                        location=loc,
                        work_model="Tam Zamanlı / Hibrit",
                        experience_level="Kurumsal Pozisyon",
                        description_text=f"{comp} bünyesinde yayınlanan {title} ilanı. Lokasyon: {loc}.",
                        apply_url=apply_url,
                        posted_date=posted_date,
                        source="corporate_verified"
                    )
                    company_jobs.append(posting)
                except Exception:
                    continue
        except Exception:
            pass

        return company_jobs

    def fetch_jobs(self) -> List[JobPosting]:
        all_jobs: List[JobPosting] = []

        # Paralel iş parçacıkları ile 30+ şirketi saniyeler içinde tara
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_target = {executor.submit(self._fetch_company_jobs, target): target for target in self.targets}
            for future in as_completed(future_to_target):
                try:
                    results = future.result()
                    all_jobs.extend(results)
                except Exception:
                    pass

        return all_jobs
