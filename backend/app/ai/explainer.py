"""
Main AI explainer service - uses enhanced implementation.
"""
import logging
from typing import Optional, Dict, Any

# Expose AI client libraries for direct access and testing
try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    from google import genai
except ImportError:
    genai = None

try:
    import boto3
except ImportError:
    boto3 = None

# Import enhanced explainer
from app.ai.explainer_enhanced import (
    redact_secrets_enhanced as redact_secrets,
    EnhancedAIExplainerService,
    EXTENDED_DETERMINISTIC_EXPLANATIONS
)
from app.core.config import settings
from app.models.finding import Finding, AIExplanation

# Update DETERMINISTIC_EXPLANATIONS to include extended ones
DETERMINISTIC_EXPLANATIONS: Dict[str, Dict[str, str]] = EXTENDED_DETERMINISTIC_EXPLANATIONS

logger = logging.getLogger(__name__)


class AIExplainerService(EnhancedAIExplainerService):
    """Main AI explainer service using enhanced implementation."""
    
    def __init__(self, cache_results: bool = True, cache_ttl: int = 3600):
        super().__init__(cache_results=cache_results, cache_ttl=cache_ttl)
        # Override provider from settings
        self.provider = settings.ai_provider

    def get_deterministic_explanation(self, finding: Finding) -> AIExplanation:
        """Get deterministic explanation with backward compatibility."""
        explanation = self.get_extended_deterministic_explanation(finding)
        explanation.provider = "deterministic-engine"
        return explanation

    def explain_finding(self, finding: Finding, file_context: Optional[str] = None) -> AIExplanation:
        """Explain finding (with caching if enabled)."""
        return self.explain_finding_with_cache(finding, file_context)


explainer_service = AIExplainerService()