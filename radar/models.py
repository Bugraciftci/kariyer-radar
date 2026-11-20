import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any


SECTORS = {
    "all": "Tüm Sektörler",
    "bank": "Bankacılık & FinTek",
    "defense": "Savunma & Havacılık",
    "tech": "E-Ticaret & Teknoloji",
    "koc": "Koç Topluluğu",
    "cosmetics": "Kozmetik & Moda / Perakende",
    "big4": "Denetim & Danışmanlık (Big 4 / MBB)",
    "telecom": "Telekomünikasyon & Altyapı",
    "fmcg": "FMCG & Gıda Devleri",
    "energy": "Enerji & Petrokimya",
    "other": "Diğer Prestijli Kurumlar"
}


@dataclass
class JobPosting:
    id: str
    company: str
    sector: str
    title: str
    location: str = "İstanbul / Türkiye"
    work_model: str = "Tam Zamanlı"
    experience_level: str = "Belirtilmemiş"
    description_text: str = ""
    requirements: List[str] = field(default_factory=list)
    apply_url: str = ""
    posted_date: Optional[str] = None
    deadline: Optional[str] = None
    source: str = "official_portal"
    is_new: bool = True
    discovered_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
    last_seen_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
    is_active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["requirements_json"] = json.dumps(self.requirements, ensure_ascii=False)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobPosting":
        reqs = data.get("requirements", [])
        if isinstance(reqs, str):
            try:
                reqs = json.loads(reqs)
            except Exception:
                reqs = [reqs]
        elif "requirements_json" in data and isinstance(data["requirements_json"], str):
            try:
                reqs = json.loads(data["requirements_json"])
            except Exception:
                reqs = []

        return cls(
            id=data["id"],
            company=data["company"],
            sector=data.get("sector", "other"),
            title=data["title"],
            location=data.get("location", "Türkiye"),
            work_model=data.get("work_model", "Tam Zamanlı"),
            experience_level=data.get("experience_level", "Belirtilmemiş"),
            description_text=data.get("description_text", ""),
            requirements=reqs,
            apply_url=data.get("apply_url", ""),
            posted_date=data.get("posted_date"),
            deadline=data.get("deadline"),
            source=data.get("source", "official_portal"),
            is_new=bool(data.get("is_new", True)),
            discovered_at=data.get("discovered_at", datetime.now().strftime("%Y-%m-%d %H:%M")),
            last_seen_at=data.get("last_seen_at", datetime.now().strftime("%Y-%m-%d %H:%M")),
            is_active=bool(data.get("is_active", True))
        )
