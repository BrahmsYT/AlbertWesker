from models import Finding

RISK_WEIGHTS: dict[str, int] = {
    "MISSING_HSTS": 10,
    "MISSING_CSP": 10,
    "MISSING_X_FRAME_OPTIONS": 7,
    "MISSING_X_CONTENT_TYPE_OPTIONS": 5,
    "MISSING_REFERRER_POLICY": 3,
    "MISSING_PERMISSIONS_POLICY": 4,
    "MISSING_X_XSS_PROTECTION": 2,
    "TLS_FAILURE": 20,
    "TLS_CERT_INVALID": 18,
    "WEAK_TLS_VERSION": 12,
    "CERT_EXPIRED": 20,
    "CERT_EXPIRING_SOON": 8,
    "SELF_SIGNED_CERT": 15,
    "WEAK_HSTS": 5,
    "NO_HTTPS_REDIRECT": 10,
    "REDIRECT_NOT_HTTPS": 6,
    "INSECURE_COOKIE": 5,
    "SERVER_INFO_DISCLOSURE": 2,
    "X_POWERED_BY_DISCLOSURE": 2,
    "DNS_RESOLUTION_FAILURE": 20,
    # AWS findings weights
    "AWS_S3_PUBLIC_BUCKET": 25,
    "AWS_S3_BUCKET_ENUMERABLE": 18,
    "AWS_CLOUDFRONT_SECURITY_WEAKNESS": 12,
    "AWS_API_GATEWAY_EXPOSED": 18,
    "AWS_ELB_HEADER_DISCLOSURE": 3,
    "AWS_IMDS_EXPOSURE_PATTERN": 16,
    "AWS_WAF_ABSENT_SIGNAL": 8,
    "AWS_ROUTE53_MISCONFIG_SIGNAL": 6,
}

# Risky open ports get dynamic codes like OPEN_PORT_3306
_PORT_RISK = 8

MAX_SCORE = 100

# Calculate max weight for normalized factor calculation
MAX_WEIGHT = max(RISK_WEIGHTS.values()) if RISK_WEIGHTS else 25


def _is_aws_finding(code: str) -> bool:
    """Check if a finding code is AWS-related."""
    return code.startswith("AWS_")


def calculate_priority(finding_code: str) -> str:
    """
    Calculate CVSS-like priority (P1-P4) based on normalized risk weight.
    Normalization uses MAX_WEIGHT (25) as baseline.
    
    Returns: "P1", "P2", "P3", or "P4"
    """
    if finding_code.startswith("OPEN_PORT_"):
        weight = _PORT_RISK
    elif finding_code.startswith("SERVICE_VERSION_"):
        weight = 3
    else:
        weight = RISK_WEIGHTS.get(finding_code, 3)
    
    # Normalize to 0-100 scale (MAX_WEIGHT=25 → 100 points)
    normalized = (weight / MAX_WEIGHT) * 100 if MAX_WEIGHT > 0 else 0
    
    if normalized >= 80:
        return "P1"
    elif normalized >= 60:
        return "P2"
    elif normalized >= 40:
        return "P3"
    else:
        return "P4"


def calculate_risk_score(findings: list[Finding]) -> tuple[int, dict]:
    """
    Calculate risk score with transparent breakdown, confidence adjustment, & priority distribution.
    Returns (final_score, score_breakdown_dict)
    
    Confidence adjustments:
    - high confidence: 100% of base weight
    - medium confidence: 70% of base weight (heuristic, may be false positive)
    - low confidence: 40% of base weight (unreliable, requires manual review)
    """
    breakdown = {
        "base_score": 0,
        "aws_score_contribution": 0,
        "confidence_adjustment": 0,
        "final_score": 0,
        "aws_findings_count": 0,
        "base_findings_count": 0,
        "base_findings": [],
        "aws_findings": [],
        "priority_distribution": {"P1": 0, "P2": 0, "P3": 0, "P4": 0},
        "confidence_distribution": {"high": 0, "medium": 0, "low": 0},
    }
    
    # Calculate base score (non-AWS findings)
    for f in findings:
        priority = calculate_priority(f.code)
        breakdown["priority_distribution"][priority] += 1
        breakdown["confidence_distribution"][f.confidence] += 1
        
        if not _is_aws_finding(f.code):
            if f.code.startswith("OPEN_PORT_"):
                weight = _PORT_RISK
            elif f.code.startswith("SERVICE_VERSION_"):
                weight = 3
            else:
                weight = RISK_WEIGHTS.get(f.code, 3)
            
            # Apply confidence multiplier
            confidence_multiplier = {
                "high": 1.0,
                "medium": 0.7,
                "low": 0.4
            }.get(f.confidence, 1.0)
            
            adjusted_weight = weight * confidence_multiplier
            breakdown["base_score"] += adjusted_weight
            breakdown["base_findings_count"] += 1
            breakdown["base_findings"].append(f.code)
        else:
            # AWS findings
            aws_weight = RISK_WEIGHTS.get(f.code, 8)
            confidence_multiplier = {
                "high": 1.0,
                "medium": 0.7,
                "low": 0.4
            }.get(f.confidence, 1.0)
            
            adjusted_aws_weight = aws_weight * confidence_multiplier
            breakdown["aws_score_contribution"] += adjusted_aws_weight
            breakdown["aws_findings_count"] += 1
            breakdown["aws_findings"].append(f.code)
    
    # Calculate confidence adjustment (penalize low-confidence findings)
    low_confidence_count = breakdown["confidence_distribution"]["low"]
    medium_confidence_count = breakdown["confidence_distribution"]["medium"]
    breakdown["confidence_adjustment"] = -(low_confidence_count * 2 + medium_confidence_count)
    
    # Calculate final score: base + aws contribution + confidence adjustment, capped at MAX_SCORE
    breakdown["final_score"] = max(0, min(
        int(breakdown["base_score"] + breakdown["aws_score_contribution"] + breakdown["confidence_adjustment"]),
        MAX_SCORE
    ))
    
    return breakdown["final_score"], breakdown


def get_risk_label(score: int) -> str:
    if score <= 20:
        return "Low"
    if score <= 50:
        return "Medium"
    if score <= 75:
        return "High"
    return "Critical"


def get_aws_risk_label(aws_score: int) -> str:
    """Get risk label specifically for AWS findings."""
    if aws_score == 0:
        return "None"
    if aws_score <= 15:
        return "Low"
    if aws_score <= 40:
        return "Medium"
    if aws_score <= 70:
        return "High"
    return "Critical"
