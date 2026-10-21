import os
import json
import logging
import subprocess
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional

from app.core.config import settings
from app.models.finding import Finding, SeverityLevel, ConfidenceLevel, FindingStatus

logger = logging.getLogger(__name__)


class GitleaksRunner:
    def __init__(self, binary_name: Optional[str] = None):
        self.binary = binary_name or settings.gitleaks_binary

    def is_available(self) -> bool:
        """Check if Gitleaks binary is installed on PATH."""
        return shutil.which(self.binary) is not None

    def run_scan(
        self,
        target_dir: Path,
        timeout: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes Gitleaks to detect hardcoded secrets and credentials in the target directory.
        Uses argument list and shell=False to prevent command injection.
        """
        if not self.is_available():
            logger.info("Gitleaks binary is not available on PATH. Skipping Gitleaks analysis.")
            return []

        timeout_sec = timeout or settings.scanner_timeout_seconds
        report_file = target_dir / f"gitleaks_report_{uuid.uuid4().hex[:6]}.json"

        # Gitleaks command: gitleaks dir <target> --no-git --report-path <report> --report-format json
        cmd: List[str] = [
            self.binary,
            "dir",
            str(target_dir),
            "--no-git",
            "--report-path",
            str(report_file),
            "--report-format",
            "json",
            "--exit-code",
            "0"  # Prevent gitleaks from exiting with non-zero on detected leaks
        ]

        logger.info(f"Executing Gitleaks: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                shell=False,
                check=False
            )

            if report_file.exists():
                try:
                    content = report_file.read_text(encoding="utf-8")
                    if content.strip():
                        findings_raw = json.loads(content)
                        return findings_raw if isinstance(findings_raw, list) else []
                finally:
                    report_file.unlink(missing_ok=True)

            return []

        except subprocess.TimeoutExpired as exc:
            logger.error(f"Gitleaks scan timed out after {timeout_sec}s")
            return []
        except Exception as e:
            logger.error(f"Gitleaks execution error: {str(e)}")
            return []


def normalize_gitleaks_findings(
    raw_leaks: List[Dict[str, Any]],
    base_dir: Path,
    scan_id: Optional[str] = None
) -> List[Finding]:
    """
    Transforms raw Gitleaks JSON leaks into normalized Finding models.
    """
    findings: List[Finding] = []

    for item in raw_leaks:
        rule_id = item.get("RuleID", "generic-api-key")
        file_path_raw = item.get("File", "")
        try:
            rel_path = os.path.relpath(file_path_raw, base_dir).replace("\\", "/")
        except Exception:
            rel_path = file_path_raw.replace("\\", "/")

        # Skip files in excluded directories (e.g. node_modules, venv, .git)
        path_parts = rel_path.split("/")
        if any(exc in path_parts for exc in settings.default_exclusions):
            continue

        start_line = item.get("StartLine", 1)
        end_line = item.get("EndLine", start_line)
        secret_match = item.get("Match", "")
        description = item.get("Description", "Exposed hardcoded credential or secret detected.")

        # Compute stable fingerprint using sanitized snippet
        fingerprint = Finding.compute_fingerprint(
            rule_id=f"gitleaks-{rule_id}",
            file_path=rel_path,
            snippet=secret_match or description
        )

        title = f"Secret Leak: {rule_id.replace('-', ' ').title()}"

        finding = Finding(
            finding_id=f"DG-{uuid.uuid4().hex[:8].upper()}",
            scan_id=scan_id,
            rule_id=f"gitleaks-{rule_id}",
            tool="gitleaks",
            title=title,
            category="hardcoded-secret",
            severity=SeverityLevel.HIGH,
            confidence=ConfidenceLevel.HIGH,
            file_path=rel_path,
            line_number=start_line,
            end_line_number=end_line,
            evidence_snippet=secret_match,
            description=description,
            impact="Exposing secrets in source code risks unauthorized access and credential compromise.",
            remediation="Immediately revoke and rotate this secret. Store credentials in environment variables or a Secrets Manager.",
            fingerprint=fingerprint,
            status=FindingStatus.NEW
        )
        findings.append(finding)

    return findings
