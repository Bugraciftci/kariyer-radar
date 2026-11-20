import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.environ.get("RADAR_DB_PATH", str(BASE_DIR / "jobs.db"))

# Default User-Agent Header
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}

# 80+ Predefined Corporates Categorized by Sector
TARGET_COMPANIES = {
    "bank": [
        "Akbank", "Garanti BBVA", "İş Bankası", "Yapı Kredi",
        "QNB Finansbank", "DenizBank", "Vakıfbank", "Halkbank",
        "Papara", "Midas", "Param", "Fibabanka", "Enpara"
    ],
    "defense": [
        "ASELSAN", "TUSAŞ", "Roketsan", "TEI", "Havelsan",
        "STM", "Baykar", "Turkish Airlines", "Pegasus", "SunExpress"
    ],
    "tech": [
        "Trendyol", "Hepsiburada", "Yemeksepeti", "Getir",
        "Sahibinden", "Insider", "Peak Games", "Dream Games",
        "Çiçeksepeti", "n11", "Martı"
    ],
    "koc": [
        "Koç Holding", "Beko", "Arçelik", "Tofaş", "Ford Otosan",
        "Tüpraş", "Otokoç", "Türk Traktör", "Koç Finansman", "Aygaz"
    ],
    "cosmetics": [
        "Gratis", "Watsons", "Sephora", "Flormar", "L'Oréal",
        "Yves Rocher", "Boyner", "Beymen", "Mavi", "LC Waikiki", "DeFacto"
    ],
    "big4": [
        "McKinsey & Company", "Boston Consulting Group (BCG)", "Bain & Company",
        "PwC Türkiye", "Deloitte Türkiye", "EY (Ernst & Young)", "KPMG Türkiye"
    ],
    "telecom": [
        "Turkcell", "Vodafone Türkiye", "Türk Telekom"
    ],
    "fmcg": [
        "Unilever", "Procter & Gamble", "Coca-Cola İçecek", "Nestlé",
        "Eti", "Ülker", "Yıldız Holding", "Hayat Kimya", "Sütaş"
    ],
    "energy": [
        "SOCAR Türkiye", "Petkim", "Enerjisa", "Opet", "Petrol Ofisi", "Shell"
    ]
}

# Mapping specific company names to their official portal strategies
OFFICIAL_PORTALS = {
    "Trendyol": "https://careers.trendyol.com",
    "Akbank": "https://kariyer.akbank.com",
    "İş Bankası": "https://ik.isbank.com.tr",
    "Turkish Airlines": "https://careers.turkishairlines.com",
    "Koç Topluluğu": "https://www.kockariyerim.com",
    "Savunma Sanayii": "https://savunmakariyer.com",
    "Turkcell": "https://kariyerim.turkcell.com.tr",
    "Getir": "https://jobs.lever.co/getir",
    "Insider": "https://jobs.lever.co/useinsider",
    "Dream Games": "https://boards.greenhouse.io/dreamgames",
    "Peak Games": "https://boards.greenhouse.io/peak"
}
