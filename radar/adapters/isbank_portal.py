import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from bs4 import BeautifulSoup
from typing import List
from radar.models import JobPosting
from radar.adapters.base import BaseJobAdapter
from radar.config import DEFAULT_HEADERS


class IsBankasiPortalAdapter(BaseJobAdapter):
    name = "Türkiye İş Bankası İK & Sınav Portalı"
    sector = "bank"
    base_url = "https://ik.isbank.com.tr"

    # Recurring high-profile banking careers
    FEATURED_POSITIONS = [
        {"slug": "mufettis-yardimcisi-20", "title": "Müfettiş Yardımcısı", "level": "Yeni Mezun / Genç Yetenek"},
        {"slug": "uzman-yardimcisi-10", "title": "Uzman Yardımcısı", "level": "Yeni Mezun / Giriş Seviyesi"},
        {"slug": "muhendis-MuhendisMHD1", "title": "Mühendis / Yazılım Geliştirici", "level": "Mühendis / Uzman"},
        {"slug": "sistem-uzmani-50", "title": "Sistem Uzmanı (IT Altyapı)", "level": "Uzman"},
        {"slug": "bilgi-teknolojileri-teknisyeni-190", "title": "Bilgi Teknolojileri Teknisyeni", "level": "Teknik Uzman"}
    ]

    def fetch_jobs(self) -> List[JobPosting]:
        jobs: List[JobPosting] = []

        # 1. Canlı İlan Listesini Kontrol Et
        try:
            res = requests.get(f"{self.base_url}/is-ilanlari-listesi", headers=DEFAULT_HEADERS, timeout=10, verify=False)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                content = soup.find("div", class_="openings__content")
                if content:
                    cards = content.find_all("div", class_="opening-card")
                    for c in cards:
                        try:
                            title_tag = c.find("h3") or c.find("a")
                            title = title_tag.get_text(strip=True) if title_tag else "Açık Pozisyon"
                            link = c.find("a", href=True)
                            apply_url = f"{self.base_url}{link['href']}" if link else f"{self.base_url}/is-ilanlari-listesi"

                            jobs.append(JobPosting(
                                id=f"isbank-live-{hash(title) % 10000000}",
                                company="Türkiye İş Bankası",
                                sector="bank",
                                title=title,
                                location="İstanbul / Türkiye Geneli",
                                work_model="Tam Zamanlı / Sınavlı İşe Alım",
                                experience_level="Sınav & Mülakat",
                                description_text=f"İş Bankası aktif işe alım ilanı: {title}. Başvuru koşulları ve sınav takvimi için resmi sayfayı inceleyin.",
                                apply_url=apply_url,
                                source="isbank_portal"
                            ))
                        except Exception:
                            continue
        except Exception as e:
            print(f"[IsBankasiPortalAdapter] Live ilan kontrolü: {e}")

        # 2. Şayet aktif sınav dönemi değilse, bankanın resmi kariyer profillerini detaylarıyla ekle
        for pos in self.FEATURED_POSITIONS:
            try:
                slug = pos["slug"]
                title = pos["title"]
                pos_url = f"{self.base_url}/pozisyon-detayi/{slug}"
                res = requests.get(pos_url, headers=DEFAULT_HEADERS, timeout=8, verify=False)
                requirements = []
                desc_text = f"Türkiye İş Bankası {title} pozisyonu genel başvuru ve kariyer programı."

                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, "html.parser")
                    paragraphs = soup.find_all("p")
                    qualifications = []
                    for p in paragraphs:
                        t = p.get_text(strip=True)
                        if any(k in t.lower() for k in ["vatandaşı olmak", "mezun olmak", "yaşını doldurmamış", "askerlik", "ingilizce", "deneyim"]):
                            qualifications.append(t)

                    if qualifications:
                        requirements = qualifications[:6]
                        desc_text = "\n".join(qualifications)

                jobs.append(JobPosting(
                    id=f"isbank-profile-{slug}",
                    company="Türkiye İş Bankası",
                    sector="bank",
                    title=title,
                    location="İstanbul (Genel Müdürlük) & Türkiye",
                    work_model="Tam Zamanlı",
                    experience_level=pos["level"],
                    description_text=desc_text,
                    requirements=requirements,
                    apply_url=pos_url,
                    source="isbank_portal"
                ))
            except Exception:
                continue

        return jobs
