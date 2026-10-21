import os
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.models.finding import Finding, SeverityLevel, ConfidenceLevel, FindingStatus


def normalize_severity(semgrep_severity: str, category: str) -> SeverityLevel:
    s = (semgrep_severity or "").upper()
    cat = (category or "").lower()

    if s == "ERROR":
        if any(keyword in cat for keyword in ["sql-injection", "command-injection", "insecure-deserialization"]):
            return SeverityLevel.CRITICAL
        return SeverityLevel.HIGH
    elif s == "WARNING":
        return SeverityLevel.MEDIUM
    elif s == "INFO":
        return SeverityLevel.LOW
    return SeverityLevel.INFORMATIONAL


def normalize_confidence(confidence_str: Optional[str]) -> ConfidenceLevel:
    if not confidence_str:
        return ConfidenceLevel.MEDIUM
    c = confidence_str.upper()
    if "HIGH" in c:
        return ConfidenceLevel.HIGH
    if "LOW" in c:
        return ConfidenceLevel.LOW
    return ConfidenceLevel.MEDIUM


def sanitize_snippet(snippet: str, max_chars: int = 400) -> str:
    """Trim and truncate snippet to avoid bloated payloads or log poisoning."""
    if not snippet:
        return ""
    clean = snippet.strip()
    if len(clean) > max_chars:
        return clean[:max_chars] + "..."
    return clean


def normalize_semgrep_findings(
    raw_data: Dict[str, Any],
    base_dir: Path,
    scan_id: Optional[str] = None
) -> List[Finding]:
    """
    Transforms raw Semgrep JSON results into unified Finding models.
    """
    findings: List[Finding] = []
    raw_results = raw_data.get("results", [])

    for item in raw_results:
        check_id = item.get("check_id", "unknown-rule")
        path_str = item.get("path", "")
        
        # Convert path to relative path with forward slashes
        try:
            rel_path = os.path.relpath(path_str, base_dir).replace("\\", "/")
        except Exception:
            rel_path = path_str.replace("\\", "/")

        start = item.get("start", {})
        end = item.get("end", {})
        line_num = start.get("line", 1)
        end_line_num = end.get("line", line_num)

        extra = item.get("extra", {})
        metadata = extra.get("metadata", {})
        message = extra.get("message", "No message provided")
        raw_snippet = extra.get("lines", "")
        clean_snippet = sanitize_snippet(raw_snippet)

        category = metadata.get("category", "general-security")
        cwe = metadata.get("cwe")
        owasp = metadata.get("owasp")
        remediation = metadata.get("remediation")

        impact_desc = None
        if cwe:
            impact_desc = f"Associated with {cwe}."
        if owasp:
            impact_desc = f"{impact_desc} OWASP: {owasp}." if impact_desc else f"OWASP: {owasp}."

        semgrep_sev = extra.get("severity", "WARNING")
        severity = normalize_severity(semgrep_sev, category)
        confidence = normalize_confidence(metadata.get("confidence"))

        # Compute stable content fingerprint
        fingerprint = Finding.compute_fingerprint(
            rule_id=check_id,
            file_path=rel_path,
            snippet=clean_snippet or message
        )

        title = check_id.replace("-", " ").replace("_", " ").title()

        finding = Finding(
            finding_id=f"DG-{uuid.uuid4().hex[:8].upper()}",
            scan_id=scan_id,
            rule_id=check_id,
            tool="semgrep",
            title=title,
            category=category,
            severity=severity,
            confidence=confidence,
            file_path=rel_path,
            line_number=line_num,
            end_line_number=end_line_num,
            evidence_snippet=clean_snippet,
            description=message,
            impact=impact_desc,
            remediation=remediation,
            fingerprint=fingerprint,
            status=FindingStatus.NEW
        )
        findings.append(finding)

    return findings
