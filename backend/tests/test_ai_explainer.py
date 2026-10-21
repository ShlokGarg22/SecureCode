from app.ai.explainer import redact_secrets, explainer_service
from app.models.finding import Finding, SeverityLevel, ConfidenceLevel, FindingStatus


def test_secret_redaction():
    exposed_text = "AWS_KEY = 'AKIAIOSFODNN7EXAMPLE' and secret_key = 'abcdef1234567890'"
    clean_text = redact_secrets(exposed_text)

    assert "AKIAIOSFODNN7EXAMPLE" not in clean_text
    assert "AKIA[REDACTED_AWS_KEY]" in clean_text
    assert "[REDACTED_SECRET]" in clean_text


def test_deterministic_explanation_fallback():
    finding = Finding(
        finding_id="DG-TEST",
        rule_id="python-sql-injection-format",
        tool="semgrep",
        title="SQL Injection Detected",
        category="sql-injection",
        severity=SeverityLevel.CRITICAL,
        confidence=ConfidenceLevel.HIGH,
        file_path="app.py",
        line_number=12,
        evidence_snippet="cursor.execute(f'SELECT * FROM users WHERE id = {user_id}')",
        description="SQL injection vulnerability",
        fingerprint="dummy_fp",
        status=FindingStatus.NEW
    )

    explanation = explainer_service.get_extended_deterministic_explanation(finding)

    assert explanation.provider == "deterministic-engine-enhanced"
    assert "parameterized" in explanation.recommended_fix.lower()
    assert explanation.attack_scenario is not None
    assert explanation.why_it_matters is not None
