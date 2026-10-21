import os
import time
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from app.core.config import settings
from app.core.extractor import validate_and_extract_zip, cleanup_directory, ArchiveSecurityError
from app.models.finding import Finding, SeverityLevel
from app.models.scan import ScanResult, SeveritySummary
from app.engine.semgrep import SemgrepRunner
from app.engine.gitleaks import GitleaksRunner, normalize_gitleaks_findings
from app.engine.normalizer import normalize_semgrep_findings
from app.ai.explainer import explainer_service
from app.db.database import save_scan_result


class ScanOrchestrator:
    def __init__(self):
        self.semgrep_runner = SemgrepRunner()
        self.gitleaks_runner = GitleaksRunner()

    def scan_project_archive(
        self,
        zip_path: Path,
        project_name: Optional[str] = None,
        rule_mode: str = "bundled",
        enable_ai: bool = True,
        custom_rules: Optional[str] = None
    ) -> ScanResult:
        scan_id = f"SCAN-{uuid.uuid4().hex[:8].upper()}"
        start_time = time.time()
        proj_name = project_name or zip_path.stem

        # Dedicated temporary isolation directory for this scan
        extract_dir = settings.data_dir / "temp_scans" / scan_id

        scanners_used: List[str] = []
        all_findings: List[Finding] = []
        files_scanned = 0
        error_msg = None

        try:
            # 1. Safely extract archive with Zip Slip and Zip Bomb prevention
            files_scanned, _ = validate_and_extract_zip(zip_path, extract_dir)

            # 2. Run Semgrep analysis
            semgrep_runner = SemgrepRunner()
            if semgrep_runner.is_available():
                scanners_used.append("semgrep")
                raw_semgrep = semgrep_runner.run_scan(
                    target_dir=extract_dir,
                    rule_mode=rule_mode,
                    custom_rule_pack=custom_rules
                )
                semgrep_findings = normalize_semgrep_findings(
                    raw_data=raw_semgrep,
                    base_dir=extract_dir,
                    scan_id=scan_id
                )
                all_findings.extend(semgrep_findings)

            gitleaks_runner = GitleaksRunner()
            if not semgrep_runner.is_available() and not gitleaks_runner.is_available():
                error_msg = "Neither Semgrep nor Gitleaks is installed on PATH. Please ensure at least one scanner is installed."

            # 3. Run Gitleaks secret detection
            if gitleaks_runner.is_available():
                scanners_used.append("gitleaks")
                raw_leaks = gitleaks_runner.run_scan(target_dir=extract_dir)
                gitleaks_findings = normalize_gitleaks_findings(
                    raw_leaks=raw_leaks,
                    base_dir=extract_dir,
                    scan_id=scan_id
                )
                all_findings.extend(gitleaks_findings)

            # 4. Enrich with Deep AI Code Context & Side-by-Side Diff
            for finding in all_findings:
                file_context = None
                try:
                    target_file = extract_dir / finding.file_path
                    if target_file.exists():
                        lines = target_file.read_text(encoding="utf-8", errors="replace").splitlines()
                        start_idx = max(0, finding.line_number - 12)
                        end_idx = min(len(lines), (finding.end_line_number or finding.line_number) + 12)
                        file_context = "\n".join(f"{i+1}: {lines[i]}" for i in range(start_idx, end_idx))
                except Exception:
                    pass

                try:
                    finding.ai_explanation = explainer_service.explain_finding(finding, file_context=file_context)
                except Exception:
                    finding.ai_explanation = explainer_service.get_deterministic_explanation(finding)

        except ArchiveSecurityError:
            raise
        except Exception as e:
            error_msg = str(e)
        finally:
            # Clean up temporary directory to avoid data leakage / disk filling
            cleanup_directory(extract_dir)

        duration = round(time.time() - start_time, 2)

        # Calculate severity summary
        severity_summary = SeveritySummary()
        for f in all_findings:
            if f.severity == SeverityLevel.CRITICAL:
                severity_summary.critical += 1
            elif f.severity == SeverityLevel.HIGH:
                severity_summary.high += 1
            elif f.severity == SeverityLevel.MEDIUM:
                severity_summary.medium += 1
            elif f.severity == SeverityLevel.LOW:
                severity_summary.low += 1
            elif f.severity == SeverityLevel.INFORMATIONAL:
                severity_summary.informational += 1

        result = ScanResult(
            scan_id=scan_id,
            project_name=proj_name,
            created_at=datetime.utcnow(),
            duration_seconds=duration,
            scanners_used=scanners_used,
            rule_mode=rule_mode,
            files_scanned=files_scanned,
            findings_count=len(all_findings),
            severity_breakdown=severity_summary,
            findings=all_findings,
            error_message=error_msg
        )

        # Persist scan result to SQLite
        save_scan_result(result)
        return result


orchestrator = ScanOrchestrator()
