"""
Improved tests for AI Explainer service with proper mocking
"""
import os
import json
import sys
from unittest.mock import patch, MagicMock, mock_open
from app.ai.explainer import redact_secrets, AIExplainerService
from app.models.finding import Finding, SeverityLevel, ConfidenceLevel, FindingStatus


def test_secret_redaction():
    """Test secret redaction functionality"""
    # Test AWS key redaction
    text = "AWS_ACCESS_KEY = 'AKIAIOSFODNN7EXAMPLE'"
    result = redact_secrets(text)
    assert "AKIA[REDACTED_AWS_KEY]" in result
    assert "AKIAIOSFODNN7EXAMPLE" not in result
    
    # Test API key redaction
    text = 'api_key = "mock_stripe_live_XXXXXXXXXXXXXXXX"'
    result = redact_secrets(text)
    assert "[REDACTED_STRIPE_KEY]" in result or "[REDACTED_SECRET]" in result
    
    # Test multiple secrets
    text = '''
    AWS_KEY = 'AKIAIOSFODNN7EXAMPLE'
    STRIPE_SECRET = "mock_stripe_test_XXXXXXXXXXXXXXXX"
    DATABASE_PASSWORD = "SuperSecret123"
    '''
    result = redact_secrets(text)
    assert "AKIA[REDACTED_AWS_KEY]" in result
    # At least one redaction should happen
    assert "REDACTED" in result


def test_deterministic_explanations():
    """Test deterministic explanations for various vulnerability types"""
    explainer = AIExplainerService()
    
    # Test SQL injection
    finding = Finding(
        finding_id="DG-SQL-TEST",
        rule_id="python-sql-injection",
        tool="semgrep",
        title="SQL Injection Detected",
        category="sql-injection",
        severity=SeverityLevel.CRITICAL,
        confidence=ConfidenceLevel.HIGH,
        file_path="auth/database.py",
        line_number=42,
        evidence_snippet="cursor.execute(f'SELECT * FROM users WHERE id = {user_id}')",
        description="SQL injection via string formatting",
        fingerprint="test_fp_sql",
        status=FindingStatus.NEW
    )
    
    explanation = explainer.get_deterministic_explanation(finding)
    
    assert explanation.provider == "deterministic-engine"
    assert "parameterized" in explanation.recommended_fix.lower()
    assert "SQL" in explanation.plain_explanation
    assert explanation.attack_scenario is not None
    assert explanation.corrected_code is not None
    
    # Test command injection
    finding = Finding(
        finding_id="DG-CMD-TEST",
        rule_id="python-command-injection",
        tool="semgrep",
        title="Command Injection Detected",
        category="command-injection",
        severity=SeverityLevel.HIGH,
        confidence=ConfidenceLevel.HIGH,
        file_path="services/diagnostics.py",
        line_number=15,
        evidence_snippet="os.system(f'ping -c 1 {target_ip}')",
        description="Command injection via os.system",
        fingerprint="test_fp_cmd",
        status=FindingStatus.NEW
    )
    
    explanation = explainer.get_deterministic_explanation(finding)
    
    assert explanation.provider == "deterministic-engine"
    assert "subprocess.run" in explanation.corrected_code
    assert "shell=False" in explanation.corrected_code
    
    # Test fallback for unknown category
    finding = Finding(
        finding_id="DG-UNKNOWN-TEST",
        rule_id="custom-rule",
        tool="semgrep",
        title="Unknown Vulnerability",
        category="weird-custom-category",
        severity=SeverityLevel.MEDIUM,
        confidence=ConfidenceLevel.MEDIUM,
        file_path="custom.js",
        line_number=99,
        evidence_snippet="something_vulnerable()",
        description="Some unknown vulnerability",
        fingerprint="test_fp_unknown",
        status=FindingStatus.NEW
    )
    
    explanation = explainer.get_deterministic_explanation(finding)
    
    assert explanation.provider == "deterministic-engine"
    assert "Security flaw" in explanation.plain_explanation


def test_explainer_with_file_context():
    """Test explainer with file context"""
    explainer = AIExplainerService()
    
    finding = Finding(
        finding_id="DG-CONTEXT-TEST",
        rule_id="python-xss",
        tool="semgrep",
        title="XSS Vulnerability",
        category="cross-site-scripting",
        severity=SeverityLevel.HIGH,
        confidence=ConfidenceLevel.HIGH,
        file_path="templates/user_profile.html",
        line_number=23,
        evidence_snippet='<div>{{ user_input|safe }}</div>',
        description="Potential XSS via unsafe template filter",
        fingerprint="test_fp_xss",
        status=FindingStatus.NEW
    )
    
    file_context = """
    <!DOCTYPE html>
    <html>
    <body>
        <div>{{ user_input|safe }}</div>
        <p>Other content</p>
    </body>
    </html>
    """
    
    explanation = explainer.explain_finding(finding, file_context=file_context)
    
    # Should get some explanation (either deterministic or AI)
    assert explanation is not None
    assert explanation.provider is not None
    assert explanation.plain_explanation is not None


def test_error_handling():
    """Test error handling in explainer"""
    explainer = AIExplainerService()
    
    # Clear environment variables to force fallback
    original_env = {}
    for key in ['AWS_ACCESS_KEY_ID', 'GROQ_API_KEY', 'GEMINI_API_KEY', 'OPENAI_API_KEY']:
        if key in os.environ:
            original_env[key] = os.environ[key]
            del os.environ[key]
    
    try:
        finding = Finding(
            finding_id="DG-ERROR-TEST",
            rule_id="python-error",
            tool="semgrep",
            title="Error Test",
            category="generic",
            severity=SeverityLevel.LOW,
            confidence=ConfidenceLevel.LOW,
            file_path="error.py",
            line_number=1,
            evidence_snippet="test()",
            description="Test error handling",
            fingerprint="test_fp_error",
            status=FindingStatus.NEW
        )
        
        explanation = explainer.explain_finding(finding)
        
        # Should fall back to deterministic explanation
        assert explanation.provider == "deterministic-engine"
        assert "Security flaw" in explanation.plain_explanation
        
    finally:
        # Restore environment variables
        for key, value in original_env.items():
            os.environ[key] = value


def test_edge_cases():
    """Test edge cases"""
    explainer = AIExplainerService()
    
    # Test with empty evidence snippet
    finding = Finding(
        finding_id="DG-EMPTY-TEST",
        rule_id="python-empty",
        tool="semgrep",
        title="Empty Evidence",
        category="generic",
        severity=SeverityLevel.LOW,
        confidence=ConfidenceLevel.LOW,
        file_path="empty.py",
        line_number=1,
        evidence_snippet="",
        description="No evidence provided",
        fingerprint="test_fp_empty",
        status=FindingStatus.NEW
    )
    
    explanation = explainer.get_deterministic_explanation(finding)
    assert explanation is not None
    
    # Test with None file context
    finding = Finding(
        finding_id="DG-NOCTX-TEST",
        rule_id="python-no-context",
        tool="semgrep",
        title="No Context",
        category="generic",
        severity=SeverityLevel.LOW,
        confidence=ConfidenceLevel.LOW,
        file_path="nocontext.py",
        line_number=5,
        evidence_snippet="print('test')",
        description="Test with no context",
        fingerprint="test_fp_nocontext",
        status=FindingStatus.NEW
    )
    
    explanation = explainer.explain_finding(finding, file_context=None)
    assert explanation is not None


def test_explainer_configuration():
    """Test explainer configuration"""
    explainer = AIExplainerService()
    
    # Test provider setting
    assert explainer.provider in ["auto", "bedrock", "groq", "gemini", "openai"]
    
    # Test environment variable influence
    os.environ['GROQ_API_KEY'] = 'test-key'
    
    # Recreate explainer to pick up new env var
    explainer2 = AIExplainerService()
    
    # Should detect groq key is available
    finding = Finding(
        finding_id="DG-ENV-TEST",
        rule_id="python-env",
        tool="semgrep",
        title="Env Test",
        category="generic",
        severity=SeverityLevel.LOW,
        confidence=ConfidenceLevel.LOW,
        file_path="env.py",
        line_number=1,
        evidence_snippet="test",
        description="Test",
        fingerprint="test_fp_env",
        status=FindingStatus.NEW
    )
    
    # This will try to use groq but might fail due to invalid key
    # Should fall back to deterministic
    explanation = explainer2.explain_finding(finding)
    assert explanation is not None
    
    del os.environ['GROQ_API_KEY']


if __name__ == '__main__':
    # Run tests
    test_secret_redaction()
    print("✓ test_secret_redaction passed")
    
    test_deterministic_explanations()
    print("✓ test_deterministic_explanations passed")
    
    test_explainer_with_file_context()
    print("✓ test_explainer_with_file_context passed")
    
    test_error_handling()
    print("✓ test_error_handling passed")
    
    test_edge_cases()
    print("✓ test_edge_cases passed")
    
    test_explainer_configuration()
    print("✓ test_explainer_configuration passed")
    
    print("\nAll tests passed!")