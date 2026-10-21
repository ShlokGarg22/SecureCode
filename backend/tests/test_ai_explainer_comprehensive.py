"""
Comprehensive tests for AI Explainer service with mock AI providers
"""
import os
import json
import unittest
from unittest.mock import patch, MagicMock
from app.ai.explainer import (
    redact_secrets, 
    AIExplainerService,
    DETERMINISTIC_EXPLANATIONS
)
from app.models.finding import Finding, SeverityLevel, ConfidenceLevel, FindingStatus
from app.models.finding import AIExplanation


class TestSecretRedaction(unittest.TestCase):
    
    def test_aws_key_redaction(self):
        """Test that AWS keys are properly redacted"""
        text = "AWS_ACCESS_KEY = 'AKIAIOSFODNN7EXAMPLE'"
        result = redact_secrets(text)
        self.assertIn("AKIA[REDACTED_AWS_KEY]", result)
        self.assertNotIn("AKIAIOSFODNN7EXAMPLE", result)
    
    def test_api_key_redaction(self):
        """Test that API keys are redacted"""
        text = 'api_key = "mock_stripe_live_XXXXXXXXXXXXXXXX"'
        result = redact_secrets(text)
        self.assertIn("[REDACTED_STRIPE_KEY]", result)
        self.assertNotIn("mock_stripe_live_XXXXXXXXXXXXXXXX", result)
    
    def test_multiple_secrets_redaction(self):
        """Test that multiple secrets in one text are all redacted"""
        text = '''
        AWS_KEY = 'AKIAIOSFODNN7EXAMPLE'
        STRIPE_SECRET = "mock_stripe_test_XXXXXXXXXXXXXXXX"
        DATABASE_PASSWORD = "SuperSecret123"
        '''
        result = redact_secrets(text)
        self.assertIn("AKIA[REDACTED_AWS_KEY]", result)
        self.assertIn("[REDACTED_SECRET]", result)


class TestDeterministicExplanations(unittest.TestCase):
    
    def setUp(self):
        self.explainer = AIExplainerService()
        
    def test_sql_injection_explanation(self):
        """Test SQL injection deterministic explanation"""
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
        
        explanation = self.explainer.get_deterministic_explanation(finding)
        
        self.assertEqual(explanation.provider, "deterministic-engine")
        self.assertIn("parameterized", explanation.recommended_fix.lower())
        self.assertIn("SQL", explanation.plain_explanation)
        self.assertIsNotNone(explanation.attack_scenario)
        self.assertIsNotNone(explanation.corrected_code)
        self.assertIsNotNone(explanation.diff_unified)
        
    def test_command_injection_explanation(self):
        """Test command injection deterministic explanation"""
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
        
        explanation = self.explainer.get_deterministic_explanation(finding)
        
        self.assertEqual(explanation.provider, "deterministic-engine")
        self.assertIn("subprocess.run", explanation.corrected_code)
        self.assertIn("shell=False", explanation.corrected_code)
        
    def test_fallback_for_unknown_category(self):
        """Test fallback explanation for unknown vulnerability category"""
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
        
        explanation = self.explainer.get_deterministic_explanation(finding)
        
        self.assertEqual(explanation.provider, "deterministic-engine")
        self.assertIn("Security flaw", explanation.plain_explanation)
        # Should still produce valid explanation even for unknown category


class TestAIExplainerServiceIntegration(unittest.TestCase):
    
    def setUp(self):
        self.explainer = AIExplainerService()
        self.sample_finding = Finding(
            finding_id="DG-INTEGRATION-TEST",
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
    
    @patch('builtins.__import__')
    def test_bedrock_integration_mock(self, mock_import):
        """Test Bedrock AI integration with mock"""
        # Configure environment for Bedrock
        os.environ['AWS_ACCESS_KEY_ID'] = 'test-key'
        os.environ['AWS_REGION'] = 'us-east-1'
        
        # Mock boto3 imports
        mock_boto3 = MagicMock()
        mock_client = MagicMock()
        mock_response = MagicMock()
        
        # Create a proper response structure
        mock_body = MagicMock()
        mock_body.read.return_value = json.dumps({
            "content": [{"text": json.dumps({
                "plain_explanation": "Test Bedrock explanation",
                "why_it_matters": "Risk from Bedrock",
                "attack_scenario": "<script>alert(1)</script>",
                "recommended_fix": "Use |escape filter",
                "original_code": "<div>{{ user_input|safe }}</div>",
                "corrected_code": "<div>{{ user_input|escape }}</div>",
                "diff_unified": "@@ -1,1 +1,1 @@\n- <div>{{ user_input|safe }}</div>\n+ <div>{{ user_input|escape }}</div>",
                "uncertainty_note": "Bedrock test note"
            })}
            ]
        }).encode()
        mock_client.invoke_model.return_value = {"body": mock_body}
        mock_boto3.client.return_value = mock_client
        
        # Mock the import
        mock_import.side_effect = lambda name, *args, **kwargs: {
            'boto3': mock_boto3
        }.get(name, __import__(name, *args, **kwargs))
        
        # Configure explainer to use bedrock
        self.explainer.provider = "bedrock"
        
        explanation = self.explainer.explain_finding(self.sample_finding)
        
        # Reset the instance to clear cached imports
        self.explainer = AIExplainerService()
        
        # Clean up
        del os.environ['AWS_ACCESS_KEY_ID']
        del os.environ['AWS_REGION']
    
    @patch('app.ai.explainer.Groq')
    def test_groq_integration_mock(self, mock_groq):
        """Test Groq AI integration with mock"""
        # Configure environment for Groq
        os.environ['GROQ_API_KEY'] = 'test-groq-key'
        
        # Mock Groq response
        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(
            content=json.dumps({
                "plain_explanation": "Test Groq explanation",
                "why_it_matters": "Risk from Groq",
                "attack_scenario": "XSS attack via unsafe filter",
                "recommended_fix": "Replace |safe with |escape",
                "original_code": "<div>{{ user_input|safe }}</div>",
                "corrected_code": "<div>{{ user_input|escape }}</div>",
                "diff_unified": "@@ -1,1 +1,1 @@\n- <div>{{ user_input|safe }}</div>\n+ <div>{{ user_input|escape }}</div>",
                "uncertainty_note": "Groq test note"
            })
        ))]
        mock_client.chat.completions.create.return_value = mock_completion
        mock_groq.return_value = mock_client
        
        # Configure explainer to use groq
        self.explainer.provider = "groq"
        
        explanation = self.explainer.explain_finding(self.sample_finding)
        
        self.assertEqual(explanation.provider, "groq")
        self.assertEqual(explanation.model, "openai/gpt-oss-20b")
        self.assertIn("Groq", explanation.plain_explanation)
        
        # Clean up
        del os.environ['GROQ_API_KEY']
    
    @patch('app.ai.explainer.genai')
    def test_gemini_integration_mock(self, mock_genai):
        """Test Google Gemini AI integration with mock"""
        # Configure environment for Gemini
        os.environ['GEMINI_API_KEY'] = 'test-gemini-key'
        
        # Mock Gemini response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "plain_explanation": "Test Gemini explanation",
            "why_it_matters": "Risk from Gemini",
            "attack_scenario": "Script injection attack",
            "recommended_fix": "Sanitize user input",
            "original_code": "<div>{{ user_input|safe }}</div>",
            "corrected_code": "<div>{{ user_input|escape }}</div>",
            "diff_unified": "@@ -1,1 +1,1 @@\n- <div>{{ user_input|safe }}</div>\n+ <div>{{ user_input|escape }}</div>",
            "uncertainty_note": "Gemini test note"
        })
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        
        # Configure explainer to use gemini
        self.explainer.provider = "gemini"
        
        explanation = self.explainer.explain_finding(self.sample_finding)
        
        self.assertEqual(explanation.provider, "google-gemini")
        self.assertEqual(explanation.model, "gemini-2.5-flash")
        self.assertIn("Gemini", explanation.plain_explanation)
        
        # Clean up
        del os.environ['GEMINI_API_KEY']
    
    def test_error_fallback(self):
        """Test that errors fall back to deterministic explanations"""
        # Clear any AI environment variables to force fallback
        if 'AWS_ACCESS_KEY_ID' in os.environ:
            del os.environ['AWS_ACCESS_KEY_ID']
        if 'GROQ_API_KEY' in os.environ:
            del os.environ['GROQ_API_KEY']
        if 'GEMINI_API_KEY' in os.environ:
            del os.environ['GEMINI_API_KEY']
        
        # Set provider to auto (should fall through to deterministic)
        self.explainer.provider = "auto"
        
        explanation = self.explainer.explain_finding(self.sample_finding)
        
        self.assertEqual(explanation.provider, "deterministic-engine")
        self.assertIn("Security flaw", explanation.plain_explanation)


class TestAIExplainerEdgeCases(unittest.TestCase):
    
    def setUp(self):
        self.explainer = AIExplainerService()
    
    def test_empty_evidence_snippet(self):
        """Test explanation with empty evidence snippet"""
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
        
        explanation = self.explainer.get_deterministic_explanation(finding)
        
        self.assertEqual(explanation.provider, "deterministic-engine")
        # Should not crash with empty snippet
        
    def test_none_context(self):
        """Test explanation with None file context"""
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
        
        explanation = self.explainer.explain_finding(finding, file_context=None)
        
        self.assertEqual(explanation.provider, "deterministic-engine")
        # Should handle None context gracefully


if __name__ == '__main__':
    unittest.main()