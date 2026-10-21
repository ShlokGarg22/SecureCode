import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from app.core.config import settings
from app.models.finding import Finding, SeverityLevel, ConfidenceLevel, FindingStatus, AIExplanation
from app.models.scan import ScanResult, SeveritySummary, ScanStatus


def init_db(db_path: Optional[Path] = None):
    target_path = db_path or settings.db_path
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(target_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                scan_id TEXT PRIMARY KEY,
                project_name TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                duration_seconds REAL NOT NULL,
                scanners_used TEXT NOT NULL,
                rule_mode TEXT NOT NULL,
                files_scanned INTEGER NOT NULL,
                findings_count INTEGER NOT NULL,
                error_message TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                finding_id TEXT PRIMARY KEY,
                scan_id TEXT NOT NULL,
                rule_id TEXT NOT NULL,
                tool TEXT NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                severity TEXT NOT NULL,
                confidence TEXT NOT NULL,
                file_path TEXT NOT NULL,
                line_number INTEGER NOT NULL,
                end_line_number INTEGER,
                evidence_snippet TEXT NOT NULL,
                description TEXT NOT NULL,
                impact TEXT,
                remediation TEXT,
                fingerprint TEXT NOT NULL,
                status TEXT NOT NULL,
                ai_explanation TEXT,
                FOREIGN KEY (scan_id) REFERENCES scans (scan_id)
            )
        """)

        # Indexes for fast query and comparison
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_findings_scan_id ON findings (scan_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_findings_fingerprint ON findings (fingerprint)")
        conn.commit()


def save_scan_result(scan_result: ScanResult, db_path: Optional[Path] = None):
    target_path = db_path or settings.db_path
    with sqlite3.connect(target_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO scans 
            (scan_id, project_name, status, created_at, duration_seconds, scanners_used, rule_mode, files_scanned, findings_count, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                scan_result.scan_id,
                scan_result.project_name,
                "completed" if not scan_result.error_message else "failed",
                scan_result.created_at.isoformat(),
                scan_result.duration_seconds,
                json.dumps(scan_result.scanners_used),
                scan_result.rule_mode,
                scan_result.files_scanned,
                scan_result.findings_count,
                scan_result.error_message
            )
        )

        for f in scan_result.findings:
            ai_json = json.dumps(f.ai_explanation.model_dump()) if f.ai_explanation else None
            cursor.execute(
                """
                INSERT OR REPLACE INTO findings
                (finding_id, scan_id, rule_id, tool, title, category, severity, confidence,
                 file_path, line_number, end_line_number, evidence_snippet, description,
                 impact, remediation, fingerprint, status, ai_explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f.finding_id,
                    scan_result.scan_id,
                    f.rule_id,
                    f.tool,
                    f.title,
                    f.category,
                    f.severity.value,
                    f.confidence.value,
                    f.file_path,
                    f.line_number,
                    f.end_line_number,
                    f.evidence_snippet,
                    f.description,
                    f.impact,
                    f.remediation,
                    f.fingerprint,
                    f.status.value,
                    ai_json
                )
            )
        conn.commit()


def get_scan(scan_id: str, db_path: Optional[Path] = None) -> Optional[ScanResult]:
    target_path = db_path or settings.db_path
    with sqlite3.connect(target_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM scans WHERE scan_id = ?", (scan_id,))
        row = cursor.fetchone()
        if not row:
            return None

        cursor.execute("SELECT * FROM findings WHERE scan_id = ?", (scan_id,))
        finding_rows = cursor.fetchall()

        findings: List[Finding] = []
        severity_summary = SeveritySummary()

        for f_row in finding_rows:
            ai_exp = None
            if f_row["ai_explanation"]:
                try:
                    ai_exp = AIExplanation(**json.loads(f_row["ai_explanation"]))
                except Exception:
                    pass

            sev = SeverityLevel(f_row["severity"])
            if sev == SeverityLevel.CRITICAL:
                severity_summary.critical += 1
            elif sev == SeverityLevel.HIGH:
                severity_summary.high += 1
            elif sev == SeverityLevel.MEDIUM:
                severity_summary.medium += 1
            elif sev == SeverityLevel.LOW:
                severity_summary.low += 1
            elif sev == SeverityLevel.INFORMATIONAL:
                severity_summary.informational += 1

            findings.append(Finding(
                finding_id=f_row["finding_id"],
                scan_id=f_row["scan_id"],
                rule_id=f_row["rule_id"],
                tool=f_row["tool"],
                title=f_row["title"],
                category=f_row["category"],
                severity=sev,
                confidence=ConfidenceLevel(f_row["confidence"]),
                file_path=f_row["file_path"],
                line_number=f_row["line_number"],
                end_line_number=f_row["end_line_number"],
                evidence_snippet=f_row["evidence_snippet"],
                description=f_row["description"],
                impact=f_row["impact"],
                remediation=f_row["remediation"],
                fingerprint=f_row["fingerprint"],
                status=FindingStatus(f_row["status"]),
                ai_explanation=ai_exp
            ))

        return ScanResult(
            scan_id=row["scan_id"],
            project_name=row["project_name"],
            created_at=datetime.fromisoformat(row["created_at"]),
            duration_seconds=row["duration_seconds"],
            scanners_used=json.loads(row["scanners_used"]),
            rule_mode=row["rule_mode"],
            files_scanned=row["files_scanned"],
            findings_count=row["findings_count"],
            severity_breakdown=severity_summary,
            findings=findings,
            error_message=row["error_message"]
        )


def list_scans(limit: int = 50, db_path: Optional[Path] = None) -> List[ScanStatus]:
    target_path = db_path or settings.db_path
    with sqlite3.connect(target_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scans ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()

        results = []
        for row in rows:
            cursor.execute("""
                SELECT severity, COUNT(*) as count 
                FROM findings 
                WHERE scan_id = ? 
                GROUP BY severity
            """, (row["scan_id"],))
            counts = {r["severity"]: r["count"] for r in cursor.fetchall()}

            summary = SeveritySummary(
                critical=counts.get("critical", 0),
                high=counts.get("high", 0),
                medium=counts.get("medium", 0),
                low=counts.get("low", 0),
                informational=counts.get("informational", 0),
            )

            results.append(ScanStatus(
                scan_id=row["scan_id"],
                project_name=row["project_name"],
                status=row["status"],
                created_at=datetime.fromisoformat(row["created_at"]),
                duration_seconds=row["duration_seconds"],
                scanners_used=json.loads(row["scanners_used"]),
                rule_mode=row["rule_mode"],
                files_scanned=row["files_scanned"],
                findings_count=row["findings_count"],
                severity_breakdown=summary,
                error_message=row["error_message"]
            ))
        return results
