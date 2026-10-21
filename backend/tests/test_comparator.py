from datetime import datetime
from app.models.finding import Finding, SeverityLevel, ConfidenceLevel, FindingStatus
from app.models.scan import ScanResult, SeveritySummary
from app.engine.comparator import compare_scans


def create_sample_finding(rule_id: str, file_path: str, snippet: str, line: int = 10) -> Finding:
    fp = Finding.compute_fingerprint(rule_id, file_path, snippet)
    return Finding(
        finding_id=f"ID-{rule_id}",
        rule_id=rule_id,
        tool="semgrep",
        title="Sample Finding",
        category="sql-injection",
        severity=SeverityLevel.HIGH,
        confidence=ConfidenceLevel.HIGH,
        file_path=file_path,
        line_number=line,
        evidence_snippet=snippet,
        description="Sample vulnerability",
        fingerprint=fp,
        status=FindingStatus.NEW
    )


def test_scan_comparison_fix_detection():
    # Base scan with 2 findings
    f1 = create_sample_finding("python-sql-injection-format", "app.py", "cursor.execute(f'SELECT {user}')", line=10)
    f2 = create_sample_finding("python-command-injection-os-system", "utils.py", "os.system(cmd)", line=25)

    base_scan = ScanResult(
        scan_id="SCAN-BASE",
        project_name="TestApp",
        created_at=datetime.utcnow(),
        duration_seconds=1.2,
        scanners_used=["semgrep"],
        rule_mode="bundled",
        files_scanned=2,
        findings_count=2,
        severity_breakdown=SeveritySummary(high=2),
        findings=[f1, f2]
    )

    # Target scan: developer fixed f1 (SQL injection is gone!), but f2 is still present (shifted to line 40)
    # Notice: f2 line number changed from 25 to 40, but snippet and rule are identical!
    f2_shifted = create_sample_finding("python-command-injection-os-system", "utils.py", "os.system(cmd)", line=40)

    target_scan = ScanResult(
        scan_id="SCAN-TARGET",
        project_name="TestApp",
        created_at=datetime.utcnow(),
        duration_seconds=1.1,
        scanners_used=["semgrep"],
        rule_mode="bundled",
        files_scanned=2,
        findings_count=1,
        severity_breakdown=SeveritySummary(high=1),
        findings=[f2_shifted]
    )

    comparison = compare_scans(base_scan, target_scan)

    # Assertions
    assert len(comparison.fixed_findings) == 1
    assert comparison.fixed_findings[0].rule_id == "python-sql-injection-format"
    assert comparison.fixed_findings[0].status == FindingStatus.FIXED

    assert len(comparison.still_present_findings) == 1
    assert comparison.still_present_findings[0].rule_id == "python-command-injection-os-system"
    assert comparison.still_present_findings[0].status == FindingStatus.STILL_PRESENT

    assert len(comparison.new_findings) == 0
    assert comparison.summary["fixed"] == 1
    assert comparison.summary["still_present"] == 1
