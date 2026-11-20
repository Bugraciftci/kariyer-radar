import re
import requests
from bs4 import BeautifulSoup
from typing import List
from radar.models import JobPosting
from radar.adapters.base import BaseJobAdapter
from radar.config import DEFAULT_HEADERS


class RoketsanPortalAdapter(BaseJobAdapter):
    name = "ROKETSAN Resmi Kariyer Portalı"
    sector = "defense"
    jobs_url = "https://kariyer.roketsan.com.tr/jobs"
    base_url = "https://kariyer.roketsan.com.tr"

    def fetch_jobs(self) -> List[JobPosting]:
        jobs: List[JobPosting] = []
        try:
            res = requests.get(self.jobs_url, headers=DEFAULT_HEADERS, timeout=15)
            if res.status_code != 200:
                return jobs
            soup = BeautifulSoup(res.text, "html.parser")
            seen = set()
            for a in soup.find_all("a", href=re.compile(r"\.job(?:\?|$)")):
                href = a.get("href", "").strip()
                if not href:
                    continue
                apply_url = href if href.startswith("http") else f"{self.base_url}/{href.lstrip('/')}"
                apply_url = apply_url.split("?")[0]
                if apply_url in seen:
                    continue
                seen.add(apply_url)
                title = re.sub(r"\s+", " ", a.get_text(" ", strip=True)).strip()
                if not title:
                    continue
                slug_id = apply_url.rstrip("/").split("/")[-1].replace(".job", "")
                jobs.append(
                    JobPosting(
                        id=f"roketsan-{slug_id}",
                        company="ROKETSAN",
                        sector="defense",
                        title=title,
                        location="Ankara, Türkiye",
                        work_model="Tam Zamanlı",
                        experience_level="Mühendis / Uzman / Teknisyen",
                        description_text=f"ROKETSAN bünyesinde açık pozisyon: {title}. Doğrudan resmi kariyer portalından başvuru yapılabilir.",
                        apply_url=apply_url,
                        source="roketsan_portal",
                    )
                )
        except Exception as e:
            print(f"[RoketsanPortalAdapter] Hata: {e}")
        return jobs


class PeakPortalAdapter(BaseJobAdapter):
    name = "Peak Games Kariyer Portalı"
    sector = "tech"
    positions_url = "https://peak.com/open-positions"
    base_url = "https://peak.com"

    def fetch_jobs(self) -> List[JobPosting]:
        jobs: List[JobPosting] = []
        try:
            res = requests.get(self.positions_url, headers=DEFAULT_HEADERS, timeout=15)
            if res.status_code != 200:
                return jobs
            soup = BeautifulSoup(res.text, "html.parser")
            seen = set()
            for a in soup.find_all("a", href=re.compile(r"/open-positions/[^/]+")):
                href = a.get("href", "").strip()
                apply_url = href if href.startswith("http") else f"{self.base_url}{href}"
                apply_url = apply_url.rstrip("/")
                if apply_url == self.positions_url or apply_url in seen:
                    continue
                seen.add(apply_url)
                title = re.sub(r"\s+", " ", a.get_text(" ", strip=True)).strip()
                if not title:
                    continue
                slug = apply_url.split("/")[-1]
                jobs.append(
                    JobPosting(
                        id=f"peak-{slug}",
                        company="Peak Games",
                        sector="tech",
                        title=title,
                        location="İstanbul, Türkiye",
                        work_model="Tam Zamanlı / Ofis",
                        experience_level="Yeni Mezun" if "new grad" in title.lower() else "Uzman / Mühendis",
                        description_text=f"Peak Games bünyesinde açılan {title} pozisyonu.",
                        apply_url=apply_url,
                        source="peak_portal",
                    )
                )
        except Exception as e:
            print(f"[PeakPortalAdapter] Hata: {e}")
        return jobs


class ExtendedAtsAdapter(BaseJobAdapter):
    name = "Genişletilmiş ATS Kurumsal İlanları (Lever/Ashby/Greenhouse)"
    sector = "tech"

    LEVER_COMPANIES = [
        ("appnation", "AppNation", "tech"),
        ("iyzico", "iyzico", "bank"),
        ("ciceksepeti", "Çiçeksepeti", "tech"),
        ("dreamgames", "Dream Games", "tech"),
        ("insiderone", "Insider One", "tech"),
        ("picus", "Picus Security", "tech"),
    ]
    ASHBY_COMPANIES = [
        ("codeway", "Codeway", "tech"),
        ("biggergames", "Bigger Games", "tech"),
    ]
    GREENHOUSE_COMPANIES = [
        ("goodjobgames", "Good Job Games", "tech"),
        ("dreamgames", "Dream Games", "tech"),
        ("sezzle", "Sezzle", "bank"),
    ]
    RECRUITEE_COMPANIES = [
        ("obilet", "Obilet", "aviation"),
    ]

    _LOCATION_FILTER_SLUGS = {"insiderone", "picus", "sezzle"}

    @staticmethod
    def _is_turkey_or_global_remote(loc: str) -> bool:
        low = (loc or "").lower()
        return any(k in low for k in ("türk", "turk", "istanbul", "ankara", "izmir"))

    def fetch_jobs(self) -> List[JobPosting]:
        jobs: List[JobPosting] = []
        seen_urls = set()

        for slug, comp, sector in self.LEVER_COMPANIES:
            try:
                res = requests.get(f"https://api.lever.co/v0/postings/{slug}?mode=json", headers=DEFAULT_HEADERS, timeout=12)
                if res.status_code != 200:
                    continue
                for item in res.json():
                    apply_url = item.get("hostedUrl") or ""
                    if not apply_url or apply_url in seen_urls:
                        continue
                    cats = item.get("categories") or {}
                    title = item.get("text", "")
                    loc = cats.get("location", "İstanbul, Türkiye")
                    if slug in self._LOCATION_FILTER_SLUGS and not self._is_turkey_or_global_remote(loc):
                        continue
                    seen_urls.add(apply_url)
                    desc = item.get("descriptionPlain", "") or title
                    jobs.append(
                        JobPosting(
                            id=f"ext-lever-{slug}-{item.get('id')}",
                            company=comp,
                            sector=sector,
                            title=title,
                            location=loc,
                            work_model=cats.get("commitment", "Tam Zamanlı"),
                            experience_level="Yeni Mezun" if "new grad" in title.lower() else ("Junior" if "junior" in title.lower() else "Uzman / Mühendis"),
                            description_text=desc[:3000],
                            apply_url=apply_url,
                            source=f"lever_{slug}",
                        )
                    )
            except Exception as e:
                print(f"[ExtendedAtsAdapter/Lever-{slug}] Hata: {e}")

        for slug, comp, sector in self.ASHBY_COMPANIES:
            try:
                res = requests.get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}", headers=DEFAULT_HEADERS, timeout=12)
                if res.status_code != 200:
                    continue
                for item in res.json().get("jobs", []):
                    apply_url = item.get("jobUrl") or ""
                    if not apply_url or apply_url in seen_urls:
                        continue
                    seen_urls.add(apply_url)
                    title = item.get("title", "")
                    loc = item.get("location", "İstanbul, Türkiye")
                    desc = item.get("descriptionPlain", "") or title
                    jobs.append(
                        JobPosting(
                            id=f"ext-ashby-{slug}-{item.get('id', hash(apply_url))}",
                            company=comp,
                            sector=sector,
                            title=title,
                            location=loc,
                            work_model="Hibrit / Ofis",
                            experience_level="Associate / Uzman" if "associate" in title.lower() else "Uzman / Mühendis",
                            description_text=desc[:3000],
                            apply_url=apply_url,
                            source=f"ashby_{slug}",
                        )
                    )
            except Exception as e:
                print(f"[ExtendedAtsAdapter/Ashby-{slug}] Hata: {e}")

        for slug, comp, sector in self.GREENHOUSE_COMPANIES:
            try:
                res = requests.get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true", headers=DEFAULT_HEADERS, timeout=12)
                if res.status_code != 200:
                    continue
                for item in res.json().get("jobs", []):
                    apply_url = item.get("absolute_url") or ""
                    if not apply_url or apply_url in seen_urls:
                        continue
                    title = item.get("title", "")
                    loc = (item.get("location") or {}).get("name", "İstanbul, Türkiye")
                    if slug in self._LOCATION_FILTER_SLUGS and not (self._is_turkey_or_global_remote(loc) or self._is_turkey_or_global_remote(title)):
                        continue
                    seen_urls.add(apply_url)
                    raw = item.get("content", "") or ""
                    clean = BeautifulSoup(raw, "html.parser").get_text(" ", strip=True) if raw else title
                    jobs.append(
                        JobPosting(
                            id=f"ext-gh-{slug}-{item.get('id')}",
                            company=comp,
                            sector=sector,
                            title=title,
                            location=loc,
                            work_model="Ofis / Hibrit",
                            experience_level="Yeni Mezun" if "new grad" in title.lower() else ("Junior" if "junior" in title.lower() else "Uzman / Mühendis"),
                            description_text=clean[:3000],
                            apply_url=apply_url,
                            source=f"greenhouse_{slug}",
                        )
                    )
            except Exception as e:
                print(f"[ExtendedAtsAdapter/GH-{slug}] Hata: {e}")

        for slug, comp, sector in self.RECRUITEE_COMPANIES:
            try:
                res = requests.get(f"https://{slug}.recruitee.com/api/offers/", headers=DEFAULT_HEADERS, timeout=12)
                if res.status_code != 200:
                    continue
                for item in res.json().get("offers", []):
                    apply_url = item.get("careers_url") or ""
                    if not apply_url or apply_url in seen_urls:
                        continue
                    seen_urls.add(apply_url)
                    title = item.get("title", "")
                    loc = item.get("location", "İstanbul, Türkiye")
                    raw = item.get("description", "") or title
                    clean = BeautifulSoup(raw, "html.parser").get_text(" ", strip=True)
                    jobs.append(
                        JobPosting(
                            id=f"ext-recruitee-{slug}-{item.get('id')}",
                            company=comp,
                            sector=sector,
                            title=title,
                            location=loc,
                            work_model="Remote" if item.get("remote") else "Hibrit / Ofis",
                            experience_level="Junior / Yeni Mezun" if any(k in title.lower() for k in ("jr", "junior", "intern", "yeni")) else "Uzman",
                            description_text=clean[:3000],
                            apply_url=apply_url,
                            source=f"recruitee_{slug}",
                        )
                    )
            except Exception as e:
                print(f"[ExtendedAtsAdapter/Recruitee-{slug}] Hata: {e}")

        return jobs
