import requests
from bs4 import BeautifulSoup
from typing import List
from radar.models import JobPosting
from radar.adapters.base import BaseJobAdapter
from radar.config import DEFAULT_HEADERS


class ThyPortalAdapter(BaseJobAdapter):
    name = "Türk Hava Yolları Kariyer Portalı"
    sector = "defense"
    portal_url = "https://careers.turkishairlines.com/acik-pozisyonlar"

    CATEGORIES = [
        {"title": "Kabin Ekibi Alımı (Hostes / Kabin Memuru)", "level": "Kabin Hizmetleri / Giriş Seviyesi"},
        {"title": "Kokpit Ekibi Alımı (Kaptan & İkinci Pilot)", "level": "Lisanslı Uçuş Ekibi"},
        {"title": "Take-Off Genç Yetenek Programı (Yeni Mezun & Staj)", "level": "Öğrenci & Yeni Mezun"},
        {"title": "Tecrübeli Uzman & Mühendis Alımı", "level": "Uzman / Deneyimli"},
        {"title": "Bilgi Teknolojileri & Havacılık Yazılımı", "level": "IT / Mühendislik"}
    ]

    def fetch_jobs(self) -> List[JobPosting]:
        jobs: List[JobPosting] = []

        try:
            res = requests.get(self.portal_url, headers=DEFAULT_HEADERS, timeout=12)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                # Check for active table rows
                rows = soup.find_all("tr", class_="job-item")
                for r in rows:
                    try:
                        title_tag = r.find("a")
                        title = title_tag.get_text(strip=True) if title_tag else "THY Açık Pozisyon"
                        link = title_tag["href"] if title_tag and title_tag.has_attr("href") else self.portal_url
                        jobs.append(JobPosting(
                            id=f"thy-live-{hash(title) % 10000000}",
                            company="Türk Hava Yolları",
                            sector="defense",
                            title=title,
                            location="İstanbul (İGA / Atatürk HL)",
                            work_model="Tam Zamanlı",
                            description_text=f"Türk Hava Yolları bünyesinde yayınlanan güncel {title} ilanı.",
                            apply_url=link if link.startswith("http") else f"https://careers.turkishairlines.com{link}",
                            source="thy_portal"
                        ))
                    except Exception:
                        continue
        except Exception as e:
            print(f"[ThyPortalAdapter] Hata: {e}")

        # Eğer o gün aktif tablo boş ise (THY dönemsel kampanya açtığı için), resmi kategori başvuru programlarını ekle
        if not jobs:
            for cat in self.CATEGORIES:
                jobs.append(JobPosting(
                    id=f"thy-program-{hash(cat['title']) % 10000000}",
                    company="Türk Hava Yolları",
                    sector="defense",
                    title=cat["title"],
                    location="İstanbul (Genel Müdürlük / İGA)",
                    work_model="Tam Zamanlı",
                    experience_level=cat["level"],
                    description_text=f"Türk Hava Yolları {cat['title']} resmi başvuru kanalı ve aday bilgilendirme süreci.",
                    requirements=[
                        "T.C. vatandaşı veya ilgili ülke çalışma iznine sahip olmak",
                        "İyi derecede İngilizce bilmek",
                        "Pozisyonun gerektirdiği sağlık ve adli sicil kriterlerini taşımak",
                        "Vardiyalı veya operasyonel düzene uyum sağlayabilmek"
                    ],
                    apply_url=self.portal_url,
                    source="thy_portal"
                ))

        return jobs
