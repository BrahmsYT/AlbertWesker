from pydantic import BaseModel, Field


class User(BaseModel):
    """User model for authentication"""
    id: int = None
    username: str
    email: str = None
    password_hash: str = None
    role: str = "user"  # "user" or "admin"
    created_at: str = None


class FrameworkMapping(BaseModel):
    framework: str          # "ISO 27001" | "NIST SP 800-53" | "SOC 2"
    control_id: str         # e.g. "A.14.1.2", "SC-8", "CC6.1"
    control_name: str
    mapping_strength: str   # "strong" | "moderate" | "weak"
    evidence_type: str      # "direct" | "indirect" | "heuristic"
    confidence: str         # "high" | "medium" | "low"
    manual_review: bool     # True when the external scan alone is insufficient


class Finding(BaseModel):
    code: str
    title: str
    severity: str  # critical, high, medium, low, info
    priority: str = "P4"  # P1 (critical), P2 (high), P3 (medium), P4 (low)
    confidence: str = "high"  # high, medium, low - indicates finding reliability
    evidence: str
    recommendation: str
    manual_review: bool = False  # True when finding requires manual verification
    frameworks: list[str]                       # legacy flat strings
    framework_mappings: list[FrameworkMapping] = Field(default_factory=list)  # rich mapping objects
    remediation_playbook: dict = Field(default_factory=dict)  # {step1: str, step2: str, ...}
    check_status: str = "passed"  # passed, failed, inconclusive, skipped
    confidence_reason: str = ""  # Explanation for confidence level assignment


class ScanResult(BaseModel):
    target: str
    risk_score: int
    risk_label: str
    findings: list[Finding]
    is_whitelisted: bool = False
    scan_meta: dict = Field(default_factory=dict)


# AWS-specific summary in scan metadata
class AWSSecuritySummary(BaseModel):
    aws_findings_count: int = 0
    aws_score_contribution: int = 0
    aws_services_detected: list[str] = Field(default_factory=list)  # CloudFront, S3, API Gateway, ELB, Route53, etc.
    aws_risk_label: str = "None"  # computed from AWS findings only
    aws_findings: list[Finding] = Field(default_factory=list)  # AWS-specific findings (subset of parent findings)
