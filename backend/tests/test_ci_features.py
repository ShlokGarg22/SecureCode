import io
import zipfile
from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from app.main import app
from app.core.config import settings
from app.core.security import create_access_token, UserRoles
from app.models.finding import Finding, SeverityLevel, ConfidenceLevel, FindingStatus, AIExplanation
from app.models.scan import ScanResult, SeveritySummary
from app.engine.patch_generator import generate_unified_patch
from app.engine.sarif_exporter import generate_sarif_report, map_severity_to_sarif_level
from app.engine.gitleaks import normalize_gitleaks_findings
from app.engine.semgrep import SemgrepRunner
from app.db.database import init_db, save_scan_result

@pytest.fixture(autouse=True)
def setup_database():
    init_db()
    token = create_access_token({"sub": "ci_tester", "role": UserRoles.ANALYST})
    client.headers.update({"Authorization": f"Bearer {token}"})

client = TestClient(app)


def test_default_exclusions_configuration():
    """Verify standard third-party folders are excluded by default."""
    expected = ["node_modules", "venv", ".venv", ".git", "__pycache__", "dist", "build"]
    for folder in expected:
        assert folder in settings.default_exclusions


def test_gitleaks_ignores_excluded_directories():
    """Verify normalize_gitleaks_findings filters out leaks located in excluded paths."""
    base_dir = Path("/mock/project")
    mock_leaks = [
        {
            "RuleID": "aws-access-token",
            "File": "/mock/project/src/auth.py",
            "StartLine": 12,
            "Match": "AKIAIOSFODNN7EXAMPLE",
            "Description": "AWS Access Key"
        },
        {
            "RuleID": "npm-token",
            "File": "/mock/project/node_modules/some-lib/index.js",
            "StartLine": 5,
            "Match": "npm_secret_sample",
            "Description": "NPM Secret in dependency"
        },
        {
            "RuleID": "pip-token",
            "File": "/mock/project/.venv/lib/site-packages/util.py",
            "StartLine": 8,
            "Match": "pypi_token_sample",
            "Description": "PyPI Secret in virtualenv"
        }
    ]

    findings = normalize_gitleaks_findings(mock_leaks, base_dir=base_dir, scan_id="TEST-SCAN")
    assert len(findings) == 1
    assert findings[0].file_path == "src/auth.py"


def test_generate_unified_patch():
    """Verify unified git patch format produces valid diff hunks for git apply."""
    finding = Finding(
        finding_id="DG-TEST1",
        rule_id="python-sqli",
        tool="semgrep",
        title="SQL Injection",
        category="sql-injection",
        description="Unsanitized user input formatted into query.",
        fingerprint="fp-test-1",
        severity=SeverityLevel.HIGH,
        confidence=ConfidenceLevel.HIGH,
        file_path="app/db.py",
        line_number=20,
        evidence_snippet="query = f'SELECT * FROM users WHERE id = {user_id}'",
        ai_explanation=AIExplanation(
            provider="fallback",
            model="deterministic",
            plain_explanation="User input is concatenated directly into SQL statement.",
            why_it_matters="Risk of database breach.",
            recommended_fix="Use parameterized queries.",
            original_code="query = f'SELECT * FROM users WHERE id = {user_id}'",
            corrected_code="query = 'SELECT * FROM users WHERE id = %s'\ncursor.execute(query, (user_id,))",
            diff_unified="--- a/app/db.py\n+++ b/app/db.py\n@@ -20,1 +20,2 @@\n-query = f'SELECT * FROM users WHERE id = {user_id}'\n+query = 'SELECT * FROM users WHERE id = %s'\n+cursor.execute(query, (user_id,))\n"
        )
    )

    patch = generate_unified_patch([finding], scan_id="SCAN-123")
    assert "SecureCode Automated Remediation Patch" in patch
    assert "--- a/app/db.py" in patch
    assert "+++ b/app/db.py" in patch
    assert "-query = f'SELECT * FROM users WHERE id = {user_id}'" in patch
    assert "+query = 'SELECT * FROM users WHERE id = %s'" in patch


def test_generate_sarif_report():
    """Verify SARIF v2.1.0 output complies with OASIS standard."""
    finding = Finding(
        finding_id="DG-TEST2",
        rule_id="hardcoded-jwt-secret",
        tool="semgrep",
        title="Hardcoded JWT Secret",
        category="hardcoded-secret",
        description="Hardcoded credential in source code.",
        fingerprint="fp-test-2",
        severity=SeverityLevel.CRITICAL,
        confidence=ConfidenceLevel.HIGH,
        file_path="auth/jwt.py",
        line_number=14,
        end_line_number=14,
        evidence_snippet="SECRET = 'supersecret123'",
        ai_explanation=AIExplanation(
            provider="fallback",
            model="deterministic",
            plain_explanation="Insecure JWT secret key.",
            why_it_matters="Compromises authentication.",
            recommended_fix="Load from os.environ.",
            original_code="SECRET = 'supersecret123'",
            corrected_code="SECRET = os.getenv('JWT_SECRET')"
        )
    )

    scan = ScanResult(
        scan_id="SCAN-SARIF-001",
        project_name="SarifTest",
        created_at=datetime.utcnow(),
        duration_seconds=1.5,
        scanners_used=["semgrep"],
        rule_mode="bundled",
        files_scanned=1,
        findings_count=1,
        severity_breakdown=SeveritySummary(critical=1),
        findings=[finding]
    )

    sarif = generate_sarif_report(scan)
    assert sarif["version"] == "2.1.0"
    assert "$schema" in sarif
    assert len(sarif["runs"]) == 1
    run = sarif["runs"][0]
    assert run["tool"]["driver"]["name"] == "DiffGuard"
    assert len(run["results"]) == 1

    result = run["results"][0]
    assert result["ruleId"] == "hardcoded-jwt-secret"
    assert result["level"] == "error"
    assert result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "auth/jwt.py"
    assert result["locations"][0]["physicalLocation"]["region"]["startLine"] == 14
    assert len(result["fixes"]) == 1
    assert result["fixes"][0]["fileChanges"][0]["replacements"][0]["insertedContent"]["text"] == "SECRET = os.getenv('JWT_SECRET')"


def test_api_export_endpoints():
    """Verify FastAPI endpoints for exporting Patch and SARIF downloads."""
    finding = Finding(
        finding_id="DG-TEST3",
        rule_id="rce-eval",
        tool="semgrep",
        title="Arbitrary Code Execution via eval",
        category="code-injection",
        description="eval() used on user input.",
        fingerprint="fp-test-3",
        severity=SeverityLevel.CRITICAL,
        confidence=ConfidenceLevel.HIGH,
        file_path="calculator.py",
        line_number=5,
        evidence_snippet="result = eval(expr)",
        ai_explanation=AIExplanation(
            provider="fallback",
            model="deterministic",
            plain_explanation="eval() executes untrusted strings.",
            why_it_matters="Remote code execution risk.",
            recommended_fix="Use ast.literal_eval.",
            original_code="result = eval(expr)",
            corrected_code="result = ast.literal_eval(expr)"
        )
    )

    scan = ScanResult(
        scan_id="SCAN-EXPORT-TEST",
        project_name="ExportTest",
        created_at=datetime.utcnow(),
        duration_seconds=0.8,
        scanners_used=["semgrep"],
        rule_mode="bundled",
        files_scanned=1,
        findings_count=1,
        severity_breakdown=SeveritySummary(critical=1),
        findings=[finding]
    )
    save_scan_result(scan)

    # Test Patch Export
    patch_res = client.get(f"/api/scans/{scan.scan_id}/export/patch")
    assert patch_res.status_code == 200
    assert "attachment; filename=remediation-SCAN-EXPORT-TEST.patch" in patch_res.headers.get("content-disposition", "")
    assert "--- a/calculator.py" in patch_res.text
    assert "+result = ast.literal_eval(expr)" in patch_res.text

    # Test SARIF Export
    sarif_res = client.get(f"/api/scans/{scan.scan_id}/export/sarif")
    assert sarif_res.status_code == 200
    sarif_json = sarif_res.json()
    assert sarif_json["version"] == "2.1.0"
    assert sarif_json["runs"][0]["results"][0]["ruleId"] == "rce-eval"

    # Test 404 for non-existent scan
    not_found = client.get("/api/scans/NON-EXISTENT/export/patch")
    assert not_found.status_code == 404
