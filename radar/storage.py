import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from radar.models import JobPosting
from radar.config import DB_PATH


class JobStorage:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS jobs (
                        id TEXT PRIMARY KEY,
                        company TEXT NOT NULL,
                        sector TEXT NOT NULL,
                        title TEXT NOT NULL,
                        location TEXT,
                        work_model TEXT,
                        experience_level TEXT,
                        description_text TEXT,
                        requirements_json TEXT,
                        apply_url TEXT,
                        posted_date TEXT,
                        deadline TEXT,
                        source TEXT,
                        is_new INTEGER DEFAULT 1,
                        discovered_at TEXT,
                        last_seen_at TEXT,
                        is_active INTEGER DEFAULT 1
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tracked_targets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        keyword TEXT UNIQUE NOT NULL,
                        sector TEXT DEFAULT 'other',
                        added_at TEXT
                    )
                """)

                cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_sector ON jobs(sector)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_is_new ON jobs(is_new)")
        finally:
            conn.close()

    def save_job(self, job: JobPosting) -> bool:
        """
        Kaydeder. İlan daha önce varsa last_seen_at güncellenir ve is_new false yapılır.
        Eğer yepyeni bir ilansa is_new = 1 kalır ve True döner.
        """
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM jobs WHERE id = ?", (job.id,))
                existing = cursor.fetchone()

                if existing:
                    cursor.execute("""
                        UPDATE jobs SET
                            company = ?, sector = ?, title = ?, location = ?,
                            work_model = ?, experience_level = ?, description_text = ?,
                            requirements_json = ?, apply_url = ?, deadline = ?,
                            last_seen_at = ?, is_active = 1
                        WHERE id = ?
                    """, (
                        job.company, job.sector, job.title, job.location,
                        job.work_model, job.experience_level, job.description_text,
                        json.dumps(job.requirements, ensure_ascii=False),
                        job.apply_url, job.deadline, now_str, job.id
                    ))
                    return False
                else:
                    cursor.execute("""
                        INSERT INTO jobs (
                            id, company, sector, title, location, work_model,
                            experience_level, description_text, requirements_json,
                            apply_url, posted_date, deadline, source, is_new,
                            discovered_at, last_seen_at, is_active
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, 1)
                    """, (
                        job.id, job.company, job.sector, job.title, job.location,
                        job.work_model, job.experience_level, job.description_text,
                        json.dumps(job.requirements, ensure_ascii=False),
                        job.apply_url, job.posted_date or now_str, job.deadline,
                        job.source, job.discovered_at or now_str, now_str
                    ))
                    return True
        finally:
            conn.close()

    def save_jobs_batch(self, jobs: List[JobPosting]) -> Tuple[int, int]:
        new_count = 0
        updated_count = 0
        for job in jobs:
            is_inserted = self.save_job(job)
            if is_inserted:
                new_count += 1
            else:
                updated_count += 1
        return new_count, updated_count

    def get_jobs(
        self,
        sector: Optional[str] = None,
        company: Optional[str] = None,
        search: Optional[str] = None,
        only_new: bool = False,
        limit: int = 150,
        offset: int = 0
    ) -> List[JobPosting]:
        query = "SELECT * FROM jobs WHERE is_active = 1"
        params = []

        if sector and sector != "all":
            query += " AND sector = ?"
            params.append(sector)

        if company:
            query += " AND company LIKE ?"
            params.append(f"%{company}%")

        if search:
            query += " AND (title LIKE ? OR company LIKE ? OR description_text LIKE ? OR location LIKE ?)"
            s_param = f"%{search}%"
            params.extend([s_param, s_param, s_param, s_param])

        if only_new:
            query += " AND is_new = 1"

        query += " ORDER BY is_new DESC, discovered_at DESC, id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [JobPosting.from_dict(dict(r)) for r in rows]
        finally:
            conn.close()

    def get_job_by_id(self, job_id: str) -> Optional[JobPosting]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs WHERE id = ? OR id LIKE ?", (job_id, f"{job_id}%"))
            row = cursor.fetchone()
            if row:
                return JobPosting.from_dict(dict(row))
            return None
        finally:
            conn.close()

    def mark_all_as_read(self):
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE jobs SET is_new = 0")
        finally:
            conn.close()

    def get_stats(self) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM jobs WHERE is_active = 1")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM jobs WHERE is_active = 1 AND is_new = 1")
            new_total = cursor.fetchone()[0]

            cursor.execute("SELECT sector, COUNT(*) FROM jobs WHERE is_active = 1 GROUP BY sector")
            by_sector = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("SELECT company, COUNT(*) FROM jobs WHERE is_active = 1 GROUP BY company ORDER BY COUNT(*) DESC LIMIT 10")
            top_companies = {row[0]: row[1] for row in cursor.fetchall()}

            return {
                "total_jobs": total,
                "new_jobs": new_total,
                "by_sector": by_sector,
                "top_companies": top_companies
            }
        finally:
            conn.close()

    def add_tracked_target(self, keyword: str, sector: str = "other") -> bool:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO tracked_targets (keyword, sector, added_at)
                    VALUES (?, ?, ?)
                """, (keyword.strip(), sector, now_str))
                return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_tracked_targets(self) -> List[Dict[str, str]]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tracked_targets ORDER BY id DESC")
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()
