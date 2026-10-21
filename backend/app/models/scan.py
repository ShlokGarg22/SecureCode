from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from app.models.finding import Finding, SeverityLevel


class SeveritySummary(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    informational: int = 0


class ScanStatus(BaseModel):
    scan_id: str
    project_name: str
    status: str  # "completed", "failed", "processing"
    created_at: datetime
    duration_seconds: float
    scanners_used: List[str]
    rule_mode: str  # "bundled", "online", "hybrid"
    files_scanned: int
    findings_count: int
    severity_breakdown: SeveritySummary
    error_message: Optional[str] = None


class ScanResult(BaseModel):
    scan_id: str
    project_name: str
    created_at: datetime
    duration_seconds: float
    scanners_used: List[str]
    rule_mode: str
    files_scanned: int
    findings_count: int
    severity_breakdown: SeveritySummary
    findings: List[Finding]
    error_message: Optional[str] = None


class ScanComparisonResult(BaseModel):
    base_scan_id: str
    target_scan_id: str
    project_name: str
    new_findings: List[Finding]
    fixed_findings: List[Finding]
    still_present_findings: List[Finding]
    uncertain_findings: List[Finding]
    summary: Dict[str, int]
