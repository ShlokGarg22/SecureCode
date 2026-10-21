from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
import hashlib


class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FindingStatus(str, Enum):
    NEW = "new"
    STILL_PRESENT = "still_present"
    FIXED = "fixed"
    UNCERTAIN = "uncertain"


class AIExplanation(BaseModel):
    provider: str = Field(..., description="AI provider used (bedrock, groq, gemini, fallback)")
    model: str = Field(..., description="Model identifier used")
    plain_explanation: str = Field(..., description="Plain-language explanation of the vulnerability")
    why_it_matters: str = Field(..., description="Security impact and risk")
    attack_scenario: Optional[str] = Field(None, description="Realistic attack scenario")
    recommended_fix: str = Field(..., description="Step-by-step remediation recommendation")
    original_code: Optional[str] = Field(None, description="Original vulnerable code snippet")
    corrected_code: Optional[str] = Field(None, description="Suggested secure code replacement")
    diff_unified: Optional[str] = Field(None, description="Unified git-style diff patch")
    line_start: Optional[int] = Field(None, description="Start line of diff block")
    line_end: Optional[int] = Field(None, description="End line of diff block")
    uncertainty_note: Optional[str] = Field(None, description="Manual verification note or caveats")


class Finding(BaseModel):
    finding_id: str = Field(..., description="Unique finding ID")
    scan_id: Optional[str] = Field(None, description="Associated scan ID")
    rule_id: str = Field(..., description="Underlying scanner rule identifier")
    tool: str = Field(..., description="Scanner tool name (semgrep, gitleaks)")
    title: str = Field(..., description="Concise finding title")
    category: str = Field(..., description="Vulnerability category (e.g. sql-injection, hardcoded-secret)")
    severity: SeverityLevel = Field(..., description="Severity rating")
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM, description="Confidence rating")
    file_path: str = Field(..., description="Normalized relative path to affected file")
    line_number: int = Field(..., ge=1, description="Starting line number")
    end_line_number: Optional[int] = Field(None, ge=1, description="Ending line number")
    evidence_snippet: str = Field(..., description="Sanitized code line or snippet")
    description: str = Field(..., description="Finding description")
    impact: Optional[str] = Field(None, description="Potential security impact")
    remediation: Optional[str] = Field(None, description="Scanner or rule remediation guidance")
    fingerprint: str = Field(..., description="Stable content-based SHA256 fingerprint")
    status: FindingStatus = Field(default=FindingStatus.NEW, description="Diff status compared to baseline")
    ai_explanation: Optional[AIExplanation] = Field(None, description="Enriched AI explanation")

    @staticmethod
    def compute_fingerprint(rule_id: str, file_path: str, snippet: str) -> str:
        """
        Compute a stable fingerprint based on rule_id, normalized file_path,
        and sanitized code content (ignoring superficial leading/trailing whitespace).
        This ensures line number shifts do not falsely invalidate existing findings.
        """
        normalized_path = file_path.replace("\\", "/").strip().lower()
        normalized_snippet = " ".join(snippet.strip().split())
        raw = f"{rule_id}:{normalized_path}:{normalized_snippet}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
