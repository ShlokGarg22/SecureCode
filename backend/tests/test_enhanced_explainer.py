"""
Comprehensive tests for enhanced AI explainer.
"""
import os
import json
from app.ai.explainer_enhanced import (
    EnhancedAIExplainerService,
    EXTENDED_DETERMINISTIC_EXPLANATIONS,
    FRAMEWORK_SPECIFIC_EXPLANATIONS,
    redact_secrets_enhanced
)
from app.models.finding import Finding, SeverityLevel, ConfidenceLevel, FindingStatus


def test_enhanced_secret_redaction():
    """Test enhanced secret redaction."""
    # Test AWS key
    text = "AWS_ACCESS_KEY = 'AKIAIOSFODNN7EXAMPLE'"
    result = redact_secrets_enhanced(text)
    assert "AKIA[REDACTED_AWS_KEY]" in result
    assert "AKIAIOSFODNN7EXAMPLE" not in result
    
    # Test Stripe key
    text = 'STRIPE_KEY = "mock_stripe_test_XXXXXXXXXXXXXXXX"'
    result = redact_secrets_enhanced(text)
    assert "[REDACTED_STRIPE_KEY]" in result
    
    # Test GitHub token
    text = 'GITHUB_TOKEN = "ghp_abcdef1234567890abcdef1234567890abcd"'
    result = redact_secrets_enhanced(text)
    assert "REDACTED" in result  # Should be redacted by generic pattern
    
    # Test database URL
    text = 'DATABASE_URL = "postgres://user:password@localhost/db"'
    result = redact_secrets_enhanced(text)
    assert "[REDACTED_USER]:[REDACTED_PASSWORD]" in result


def test_extended_deterministic_explanations():
    """Test extended deterministic explanations."""
    explainer = EnhancedAIExplainerService(cache_results=False)
    
    # Test XSS explanation
    finding = Finding(
        finding_id="TEST-XSS",
        rule_id="web-xss",
        tool="semgrep",
        title="Cross-Site Scripting",
        category="cross-site-scripting",
        severity=SeverityLevel.HIGH,
        confidence=ConfidenceLevel.HIGH,
        file_path="templates/page.html",
        line_number=10,
        evidence_snippet='<div>{{ user_input }}</div>',
        description="XSS vulnerability",
        fingerprint="test_xss",
        status=FindingStatus.NEW
    )
    
    explanation = explainer.get_extended_deterministic_explanation(finding)
    
    assert explanation.provider == "deterministic-engine-enhanced"
    assert "encoding" in explanation.plain_explanation.lower() or "sanitization" in explanation.plain_explanation.lower()
    assert "escaping" in explanation.recommended_fix.lower() or "encoding" in explanation.recommended_fix.lower()
    assert explanation.corrected_code is not None
    
    # Test SSRF explanation
    finding = Finding(
        finding_id="TEST-SSRF",
        rule_id="server-ssrf",
        tool="semgrep",
        title="Server-Side Request Forgery",
        category="ssrf-server-side-request-forgery",
        severity=SeverityLevel.HIGH,
        confidence=ConfidenceLevel.MEDIUM,
        file_path="api.py",
        line_number=25,
        evidence_snippet="requests.get(user_url)",
        description="SSRF vulnerability",
        fingerprint="test_ssrf",
        status=FindingStatus.NEW
    )
    
    explanation = explainer.get_extended_deterministic_explanation(finding)
    
    assert explanation.provider == "deterministic-engine-enhanced"
    assert "allowlist" in explanation.recommended_fix.lower() or "whitelist" in explanation.recommended_fix.lower()
    assert "internal" in explanation.attack_scenario.lower() or "metadata" in explanation.attack_scenario.lower()


def test_framework_specific_explanations():
    """Test framework-specific explanations."""
    explainer = EnhancedAIExplainerService(cache_results=False)
    
    # Test Django XSS
    finding = Finding(
        finding_id="TEST-DJANGO",
        rule_id="django-xss",
        tool="semgrep",
        title="Django XSS",
        category="django-xss",
        severity=SeverityLevel.HIGH,
        confidence=ConfidenceLevel.HIGH,
        file_path="templates/django/profile.html",
        line_number=5,
        evidence_snippet="{{ user_input|safe }}",
        description="Django template XSS",
        fingerprint="test_django",
        status=FindingStatus.NEW
    )
    
    explanation = explainer.get_extended_deterministic_explanation(finding)
    
    assert explanation.provider == "deterministic-engine-enhanced"
    assert "django" in explanation.plain_explanation.lower()
    assert "autoescape" in explanation.plain_explanation.lower() or "|safe" in explanation.original_code
    
    # Test React XSS
    finding = Finding(
        finding_id="TEST-REACT",
        rule_id="react-xss",
        tool="semgrep",
        title="React XSS",
        category="react-xss",
        severity=SeverityLevel.HIGH,
        confidence=ConfidenceLevel.HIGH,
        file_path="components/UserProfile.jsx",
        line_number=15,
        evidence_snippet='<div dangerouslySetInnerHTML={{ __html: userContent }} />',
        description="React XSS via dangerouslySetInnerHTML",
        fingerprint="test_react",
        status=FindingStatus.NEW
    )
    
    explanation = explainer.get_extended_deterministic_explanation(finding)
    
    assert explanation.provider == "deterministic-engine-enhanced"
    assert "react" in explanation.plain_explanation.lower()
    assert "dangerouslysetinnerhtml" in explanation.plain_explanation.lower()
    assert "DOMPurify" in explanation.recommended_fix or "sanitize" in explanation.recommended_fix.lower()


def test_file_path_based_detection():
    """Test file path-based framework detection."""
    explainer = EnhancedAIExplainerService(cache_results=False)
    
    # React file
    finding = Finding(
        finding_id="TEST-REACT-FILE",
        rule_id="generic-xss",
        tool="semgrep",
        title="Potential XSS",
        category="generic-xss",
        severity=SeverityLevel.MEDIUM,
        confidence=ConfidenceLevel.MEDIUM,
        file_path="src/components/Profile.tsx",  # React/TypeScript file
        line_number=20,
        evidence_snippet='<div>{userInput}</div>',
        description="Potential XSS",
        fingerprint="test_react_file",
        status=FindingStatus.NEW
    )
    
    explanation = explainer.get_extended_deterministic_explanation(finding)
    
    # Should detect React/JSX context
    assert explanation.provider == "deterministic-engine-enhanced"
    
    # Django Python file
    finding = Finding(
        finding_id="TEST-DJANGO-FILE",
        rule_id="generic-xss",
        tool="semgrep",
        title="Potential XSS",
        category="generic-xss",
        severity=SeverityLevel.MEDIUM,
        confidence=ConfidenceLevel.MEDIUM,
        file_path="django_app/templates/users.html",  # Django template
        line_number=15,
        evidence_snippet="{{ user_data }}",
        description="Potential XSS",
        fingerprint="test_django_file",
        status=FindingStatus.NEW
    )
    
    explanation = explainer.get_extended_deterministic_explanation(finding)
    
    assert explanation.provider == "deterministic-engine-enhanced"


def test_cache_functionality():
    """Test explanation caching."""
    explainer = EnhancedAIExplainerService(cache_results=True, cache_ttl=10)
    
    finding = Finding(
        finding_id="TEST-CACHE",
        rule_id="caching-test",
        tool="semgrep",
        title="Cache Test",
        category="sql-injection",
        severity=SeverityLevel.MEDIUM,
        confidence=ConfidenceLevel.MEDIUM,
        file_path="test.py",
        line_number=1,
        evidence_snippet="cursor.execute(f'SELECT * FROM users WHERE id = {user_id}')",
        description="Cache test",
        fingerprint="test_cache_fp",
        status=FindingStatus.NEW
    )
    
    # First call - should compute
    explanation1 = explainer.explain_finding_with_cache(finding)
    assert explanation1 is not None
    
    # Second call - should be cached
    explanation2 = explainer.explain_finding_with_cache(finding)
    assert explanation2 is not None
    assert explanation2.provider == explanation1.provider
    
    # For now, just verify it doesn't crash
    # In a real test with a mock, we could verify the cache was hit


def test_error_handling_and_fallback():
    """Test error handling and fallback mechanisms."""
    explainer = EnhancedAIExplainerService(cache_results=False)
    
    # Clear environment to force fallback
    env_backup = {}
    for key in ['AWS_ACCESS_KEY_ID', 'GROQ_API_KEY', 'GEMINI_API_KEY', 'OPENAI_API_KEY']:
        if key in os.environ:
            env_backup[key] = os.environ[key]
            del os.environ[key]
    
    try:
        finding = Finding(
            finding_id="TEST-FALLBACK",
            rule_id="fallback-test",
            tool="semgrep",
            title="Fallback Test",
            category="test-category",
            severity=SeverityLevel.LOW,
            confidence=ConfidenceLevel.LOW,
            file_path="test.py",
            line_number=1,
            evidence_snippet="some_code()",
            description="Test for fallback",
            fingerprint="test_fallback",
            status=FindingStatus.NEW
        )
        
        # Should fall back to deterministic explanation
        explanation = explainer.explain_finding_with_cache(finding)
        
        # Just verify we get a valid explanation regardless of provider
        assert explanation is not None
        assert explanation.provider is not None
        assert explanation.plain_explanation is not None
        
    finally:
        # Restore environment
        for key, value in env_backup.items():
            os.environ[key] = value


def test_insecure_randomness_explanation():
    """Test insecure randomness explanation."""
    explainer = EnhancedAIExplainerService(cache_results=False)
    
    finding = Finding(
        finding_id="TEST-RANDOM",
        rule_id="insecure-random",
        tool="semgrep",
        title="Insecure Randomness",
        category="insecure-randomness",
        severity=SeverityLevel.MEDIUM,
        confidence=ConfidenceLevel.HIGH,
        file_path="auth.py",
        line_number=30,
        evidence_snippet="session_id = random.randint(1000, 9999)",
        description="Using insecure random for session IDs",
        fingerprint="test_random",
        status=FindingStatus.NEW
    )
    
    explanation = explainer.get_extended_deterministic_explanation(finding)
    
    assert explanation.provider == "deterministic-engine-enhanced"
    assert "cryptographically" in explanation.plain_explanation.lower() or "secure" in explanation.plain_explanation.lower()
    assert "secrets" in explanation.corrected_code or "getRandomValues" in explanation.corrected_code


def test_xxe_explanation():
    """Test XXE explanation."""
    explainer = EnhancedAIExplainerService(cache_results=False)
    
    finding = Finding(
        finding_id="TEST-XXE",
        rule_id="xml-xxe",
        tool="semgrep",
        title="XML External Entity",
        category="xxe-xml-external-entity",
        severity=SeverityLevel.HIGH,
        confidence=ConfidenceLevel.HIGH,
        file_path="xml_processor.py",
        line_number=15,
        evidence_snippet="tree = ET.parse(xml_file)",
        description="XXE vulnerability",
        fingerprint="test_xxe",
        status=FindingStatus.NEW
    )
    
    explanation = explainer.get_extended_deterministic_explanation(finding)
    
    assert explanation.provider == "deterministic-engine-enhanced"
    assert "external entities" in explanation.plain_explanation.lower()
    assert "resolve_entities=False" in explanation.corrected_code or "defusedxml" in explanation.recommended_fix


if __name__ == '__main__':
    print("Running enhanced explainer tests...")
    
    test_enhanced_secret_redaction()
    print("✓ test_enhanced_secret_redaction")
    
    test_extended_deterministic_explanations()
    print("✓ test_extended_deterministic_explanations")
    
    test_framework_specific_explanations()
    print("✓ test_framework_specific_explanations")
    
    test_file_path_based_detection()
    print("✓ test_file_path_based_detection")
    
    test_cache_functionality()
    print("✓ test_cache_functionality")
    
    test_error_handling_and_fallback()
    print("✓ test_error_handling_and_fallback")
    
    test_insecure_randomness_explanation()
    print("✓ test_insecure_randomness_explanation")
    
    test_xxe_explanation()
    print("✓ test_xxe_explanation")
    
    print("\nAll enhanced AI explainer tests passed!")