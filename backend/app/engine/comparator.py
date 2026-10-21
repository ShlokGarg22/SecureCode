from typing import List, Dict, Set
from app.models.finding import Finding, FindingStatus
from app.models.scan import ScanResult, ScanComparisonResult


def compare_scans(base_scan: ScanResult, target_scan: ScanResult) -> ScanComparisonResult:
    """
    Compares two scans of a project to determine which vulnerabilities
    have been fixed, which are still present, and which are newly introduced.
    
    Uses content-based stable fingerprints to avoid false results caused by line shifts.
    """
    base_fingerprints: Dict[str, Finding] = {f.fingerprint: f for f in base_scan.findings}
    target_fingerprints: Dict[str, Finding] = {f.fingerprint: f for f in target_scan.findings}

    new_findings: List[Finding] = []
    fixed_findings: List[Finding] = []
    still_present_findings: List[Finding] = []
    uncertain_findings: List[Finding] = []

    # Check target findings against baseline
    for fp, finding in target_fingerprints.items():
        if fp in base_fingerprints:
            finding_copy = finding.model_copy(update={"status": FindingStatus.STILL_PRESENT})
            still_present_findings.append(finding_copy)
        else:
            # Check if this might be an uncertain match (same rule_id and file_path, but modified code context)
            partial_matches = [
                bf for bf in base_scan.findings
                if bf.rule_id == finding.rule_id and bf.file_path == finding.file_path
                and bf.fingerprint not in target_fingerprints
            ]
            if partial_matches:
                finding_copy = finding.model_copy(update={"status": FindingStatus.UNCERTAIN})
                uncertain_findings.append(finding_copy)
            else:
                finding_copy = finding.model_copy(update={"status": FindingStatus.NEW})
                new_findings.append(finding_copy)

    # Check baseline findings not found in target
    matched_or_uncertain_base_fps: Set[str] = {f.fingerprint for f in still_present_findings}
    for uf in uncertain_findings:
        for bf in base_scan.findings:
            if bf.rule_id == uf.rule_id and bf.file_path == uf.file_path:
                matched_or_uncertain_base_fps.add(bf.fingerprint)

    for fp, base_finding in base_fingerprints.items():
        if fp not in matched_or_uncertain_base_fps:
            fixed_copy = base_finding.model_copy(update={"status": FindingStatus.FIXED})
            fixed_findings.append(fixed_copy)

    summary = {
        "new": len(new_findings),
        "fixed": len(fixed_findings),
        "still_present": len(still_present_findings),
        "uncertain": len(uncertain_findings),
        "total_current": len(target_scan.findings)
    }

    return ScanComparisonResult(
        base_scan_id=base_scan.scan_id,
        target_scan_id=target_scan.scan_id,
        project_name=target_scan.project_name,
        new_findings=new_findings,
        fixed_findings=fixed_findings,
        still_present_findings=still_present_findings,
        uncertain_findings=uncertain_findings,
        summary=summary
    )
