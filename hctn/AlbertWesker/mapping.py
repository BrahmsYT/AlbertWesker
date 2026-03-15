"""
Compliance-framework mapping module.

IMPORTANT DESIGN NOTES
─────────────────────
This scanner performs *external, non-intrusive* checks only (HTTP headers, TLS
handshake, port probes, DNS).  It can never confirm full compliance with any
framework.  Every mapping therefore carries metadata that describes HOW STRONG
the link between the technical finding and the framework control actually is:

  mapping_strength  – strong / moderate / weak
  evidence_type     – direct / indirect / heuristic
  confidence        – high / medium / low  (how sure we are the signal is real)
  manual_review     – True when the finding alone is NOT enough to judge the control
"""

from __future__ import annotations


# ────────────────────────────────────────────
# Mapping-entry structure (one per framework per finding code)
# ────────────────────────────────────────────
# Each value in COMPLIANCE_MAP is a list of dicts with these keys:
#   framework        : "ISO 27001" | "NIST SP 800-53" | "SOC 2"
#   control_id       : e.g. "A.14.1.2", "SC-8", "CC6.1"
#   control_name     : human-readable title
#   mapping_strength : "strong" | "moderate" | "weak"
#   evidence_type    : "direct" | "indirect" | "heuristic"
#   confidence       : "high" | "medium" | "low"
#   manual_review    : bool – True when external scan cannot fully assess

COMPLIANCE_MAP: dict[str, list[dict]] = {
    # ── HTTP security headers ──────────────────────
    "MISSING_HSTS": [
        {"framework": "ISO 27001", "control_id": "A.14.1.2", "control_name": "Securing application services on public networks",
         "mapping_strength": "strong", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "NIST SP 800-53", "control_id": "SC-8", "control_name": "Transmission Confidentiality and Integrity",
         "mapping_strength": "moderate", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "SOC 2", "control_id": "CC6.1", "control_name": "Logical and Physical Access Controls",
         "mapping_strength": "weak", "evidence_type": "indirect", "confidence": "medium", "manual_review": True},
    ],
    "MISSING_CSP": [
        {"framework": "ISO 27001", "control_id": "A.14.2.5", "control_name": "Secure system engineering principles",
         "mapping_strength": "moderate", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "NIST SP 800-53", "control_id": "SI-3", "control_name": "Malicious Code Protection",
         "mapping_strength": "weak", "evidence_type": "indirect", "confidence": "medium", "manual_review": True},
        {"framework": "SOC 2", "control_id": "CC6.1", "control_name": "Logical and Physical Access Controls",
         "mapping_strength": "weak", "evidence_type": "indirect", "confidence": "medium", "manual_review": True},
    ],
    "MISSING_X_FRAME_OPTIONS": [
        {"framework": "ISO 27001", "control_id": "A.14.1.2", "control_name": "Securing application services on public networks",
         "mapping_strength": "moderate", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "NIST SP 800-53", "control_id": "SI-3", "control_name": "Malicious Code Protection",
         "mapping_strength": "weak", "evidence_type": "indirect", "confidence": "medium", "manual_review": True},
        {"framework": "SOC 2", "control_id": "CC6.1", "control_name": "Logical and Physical Access Controls",
         "mapping_strength": "weak", "evidence_type": "indirect", "confidence": "medium", "manual_review": True},
    ],
    "MISSING_X_CONTENT_TYPE_OPTIONS": [
        {"framework": "ISO 27001", "control_id": "A.14.1.2", "control_name": "Securing application services on public networks",
         "mapping_strength": "moderate", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "NIST SP 800-53", "control_id": "SI-3", "control_name": "Malicious Code Protection",
         "mapping_strength": "weak", "evidence_type": "indirect", "confidence": "medium", "manual_review": True},
        {"framework": "SOC 2", "control_id": "CC6.6", "control_name": "Security Event Monitoring",
         "mapping_strength": "weak", "evidence_type": "heuristic", "confidence": "low", "manual_review": True},
    ],
    "MISSING_REFERRER_POLICY": [
        {"framework": "ISO 27001", "control_id": "A.18.1.4", "control_name": "Privacy and protection of PII",
         "mapping_strength": "weak", "evidence_type": "indirect", "confidence": "medium", "manual_review": True},
        {"framework": "NIST SP 800-53", "control_id": "AC-4", "control_name": "Information Flow Enforcement",
         "mapping_strength": "weak", "evidence_type": "indirect", "confidence": "low", "manual_review": True},
        {"framework": "SOC 2", "control_id": "CC6.1", "control_name": "Logical and Physical Access Controls",
         "mapping_strength": "weak", "evidence_type": "heuristic", "confidence": "low", "manual_review": True},
    ],
    "MISSING_PERMISSIONS_POLICY": [
        {"framework": "ISO 27001", "control_id": "A.14.2.5", "control_name": "Secure system engineering principles",
         "mapping_strength": "weak", "evidence_type": "indirect", "confidence": "medium", "manual_review": True},
        {"framework": "NIST SP 800-53", "control_id": "CM-7", "control_name": "Least Functionality",
         "mapping_strength": "moderate", "evidence_type": "indirect", "confidence": "medium", "manual_review": True},
        {"framework": "SOC 2", "control_id": "CC6.1", "control_name": "Logical and Physical Access Controls",
         "mapping_strength": "weak", "evidence_type": "heuristic", "confidence": "low", "manual_review": True},
    ],
    "MISSING_X_XSS_PROTECTION": [
        {"framework": "ISO 27001", "control_id": "A.14.2.5", "control_name": "Secure system engineering principles",
         "mapping_strength": "weak", "evidence_type": "indirect", "confidence": "low", "manual_review": True},
        {"framework": "NIST SP 800-53", "control_id": "SI-3", "control_name": "Malicious Code Protection",
         "mapping_strength": "weak", "evidence_type": "heuristic", "confidence": "low", "manual_review": True},
        {"framework": "SOC 2", "control_id": "CC6.1", "control_name": "Logical and Physical Access Controls",
         "mapping_strength": "weak", "evidence_type": "heuristic", "confidence": "low", "manual_review": True},
    ],

    # ── TLS / Certificate ──────────────────────────
    "TLS_FAILURE": [
        {"framework": "ISO 27001", "control_id": "A.10.1.1", "control_name": "Cryptographic controls",
         "mapping_strength": "strong", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "NIST SP 800-53", "control_id": "SC-8", "control_name": "Transmission Confidentiality and Integrity",
         "mapping_strength": "strong", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "SOC 2", "control_id": "CC6.7", "control_name": "Encryption of Data in Transit",
         "mapping_strength": "strong", "evidence_type": "direct", "confidence": "high", "manual_review": False},
    ],
    "TLS_CERT_INVALID": [
        {"framework": "ISO 27001", "control_id": "A.10.1.2", "control_name": "Key management",
         "mapping_strength": "strong", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "NIST SP 800-53", "control_id": "SC-17", "control_name": "Public Key Infrastructure Certificates",
         "mapping_strength": "strong", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "SOC 2", "control_id": "CC6.7", "control_name": "Encryption of Data in Transit",
         "mapping_strength": "strong", "evidence_type": "direct", "confidence": "high", "manual_review": False},
    ],
    "WEAK_TLS_VERSION": [
        {"framework": "ISO 27001", "control_id": "A.10.1.1", "control_name": "Cryptographic controls",
         "mapping_strength": "strong", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "NIST SP 800-53", "control_id": "SC-13", "control_name": "Cryptographic Protection",
         "mapping_strength": "strong", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "SOC 2", "control_id": "CC6.1", "control_name": "Logical and Physical Access Controls",
         "mapping_strength": "moderate", "evidence_type": "direct", "confidence": "high", "manual_review": False},
    ],
    "CERT_EXPIRED": [
        {"framework": "ISO 27001", "control_id": "A.10.1.2", "control_name": "Key management",
         "mapping_strength": "strong", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "NIST SP 800-53", "control_id": "SC-17", "control_name": "Public Key Infrastructure Certificates",
         "mapping_strength": "strong", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "SOC 2", "control_id": "CC6.7", "control_name": "Encryption of Data in Transit",
         "mapping_strength": "strong", "evidence_type": "direct", "confidence": "high", "manual_review": False},
    ],
    "CERT_EXPIRING_SOON": [
        {"framework": "ISO 27001", "control_id": "A.10.1.2", "control_name": "Key management",
         "mapping_strength": "moderate", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "NIST SP 800-53", "control_id": "SC-17", "control_name": "Public Key Infrastructure Certificates",
         "mapping_strength": "moderate", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "SOC 2", "control_id": "CC7.1", "control_name": "Detection of Changes",
         "mapping_strength": "moderate", "evidence_type": "indirect", "confidence": "medium", "manual_review": True},
    ],
    "SELF_SIGNED_CERT": [
        {"framework": "ISO 27001", "control_id": "A.10.1.2", "control_name": "Key management",
         "mapping_strength": "strong", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "NIST SP 800-53", "control_id": "SC-17", "control_name": "Public Key Infrastructure Certificates",
         "mapping_strength": "strong", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "SOC 2", "control_id": "CC6.7", "control_name": "Encryption of Data in Transit",
         "mapping_strength": "moderate", "evidence_type": "direct", "confidence": "high", "manual_review": False},
    ],

    # ── HTTPS redirect ─────────────────────────────
    "WEAK_HSTS": [
        {"framework": "ISO 27001", "control_id": "A.14.1.2", "control_name": "Securing application services on public networks",
         "mapping_strength": "moderate", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "NIST SP 800-53", "control_id": "SC-8", "control_name": "Transmission Confidentiality and Integrity",
         "mapping_strength": "moderate", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "SOC 2", "control_id": "CC6.1", "control_name": "Logical and Physical Access Controls",
         "mapping_strength": "weak", "evidence_type": "indirect", "confidence": "medium", "manual_review": True},
    ],
    "NO_HTTPS_REDIRECT": [
        {"framework": "ISO 27001", "control_id": "A.14.1.2", "control_name": "Securing application services on public networks",
         "mapping_strength": "strong", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "NIST SP 800-53", "control_id": "SC-8", "control_name": "Transmission Confidentiality and Integrity",
         "mapping_strength": "strong", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "SOC 2", "control_id": "CC6.7", "control_name": "Encryption of Data in Transit",
         "mapping_strength": "moderate", "evidence_type": "direct", "confidence": "high", "manual_review": False},
    ],
    "REDIRECT_NOT_HTTPS": [
        {"framework": "ISO 27001", "control_id": "A.14.1.2", "control_name": "Securing application services on public networks",
         "mapping_strength": "moderate", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "NIST SP 800-53", "control_id": "SC-8", "control_name": "Transmission Confidentiality and Integrity",
         "mapping_strength": "moderate", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "SOC 2", "control_id": "CC6.7", "control_name": "Encryption of Data in Transit",
         "mapping_strength": "moderate", "evidence_type": "direct", "confidence": "medium", "manual_review": True},
    ],

    # ── Cookie / Session ───────────────────────────
    "INSECURE_COOKIE": [
        {"framework": "ISO 27001", "control_id": "A.14.1.3", "control_name": "Protecting application service transactions",
         "mapping_strength": "moderate", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "NIST SP 800-53", "control_id": "SC-23", "control_name": "Session Authenticity",
         "mapping_strength": "moderate", "evidence_type": "direct", "confidence": "medium", "manual_review": True},
        {"framework": "SOC 2", "control_id": "CC6.1", "control_name": "Logical and Physical Access Controls",
         "mapping_strength": "weak", "evidence_type": "indirect", "confidence": "medium", "manual_review": True},
    ],

    # ── Information disclosure ─────────────────────
    "SERVER_INFO_DISCLOSURE": [
        {"framework": "ISO 27001", "control_id": "A.12.6.1", "control_name": "Management of technical vulnerabilities",
         "mapping_strength": "weak", "evidence_type": "heuristic", "confidence": "medium", "manual_review": True},
        {"framework": "NIST SP 800-53", "control_id": "SI-11", "control_name": "Error Handling",
         "mapping_strength": "weak", "evidence_type": "heuristic", "confidence": "medium", "manual_review": True},
        {"framework": "SOC 2", "control_id": "CC6.6", "control_name": "Security Event Monitoring",
         "mapping_strength": "weak", "evidence_type": "heuristic", "confidence": "low", "manual_review": True},
    ],
    "X_POWERED_BY_DISCLOSURE": [
        {"framework": "ISO 27001", "control_id": "A.12.6.1", "control_name": "Management of technical vulnerabilities",
         "mapping_strength": "weak", "evidence_type": "heuristic", "confidence": "medium", "manual_review": True},
        {"framework": "NIST SP 800-53", "control_id": "SI-11", "control_name": "Error Handling",
         "mapping_strength": "weak", "evidence_type": "heuristic", "confidence": "medium", "manual_review": True},
        {"framework": "SOC 2", "control_id": "CC6.6", "control_name": "Security Event Monitoring",
         "mapping_strength": "weak", "evidence_type": "heuristic", "confidence": "low", "manual_review": True},
    ],

    # ── DNS ────────────────────────────────────────
    "DNS_RESOLUTION_FAILURE": [
        {"framework": "ISO 27001", "control_id": "A.13.1.1", "control_name": "Network controls",
         "mapping_strength": "moderate", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "NIST SP 800-53", "control_id": "SC-20", "control_name": "Secure Name / Address Resolution Service",
         "mapping_strength": "moderate", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "SOC 2", "control_id": "CC6.1", "control_name": "Logical and Physical Access Controls",
         "mapping_strength": "weak", "evidence_type": "indirect", "confidence": "medium", "manual_review": True},
    ],

    # ── AWS Security Findings ──────────────────────
    "AWS_S3_PUBLIC_BUCKET": [
        {"framework": "ISO 27001", "control_id": "A.14.1.2", "control_name": "Securing application services on public networks",
         "mapping_strength": "strong", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "NIST SP 800-53", "control_id": "AC-3", "control_name": "Access Enforcement",
         "mapping_strength": "strong", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "SOC 2", "control_id": "CC6.1", "control_name": "Logical and Physical Access Controls",
         "mapping_strength": "strong", "evidence_type": "direct", "confidence": "high", "manual_review": False},
    ],
    "AWS_S3_BUCKET_ENUMERABLE": [
        {"framework": "ISO 27001", "control_id": "A.14.1.2", "control_name": "Securing application services on public networks",
         "mapping_strength": "moderate", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "NIST SP 800-53", "control_id": "AC-3", "control_name": "Access Enforcement",
         "mapping_strength": "moderate", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "SOC 2", "control_id": "CC6.1", "control_name": "Logical and Physical Access Controls",
         "mapping_strength": "moderate", "evidence_type": "direct", "confidence": "high", "manual_review": False},
    ],
    "AWS_CLOUDFRONT_SECURITY_WEAKNESS": [
        {"framework": "ISO 27001", "control_id": "A.14.1.2", "control_name": "Securing application services on public networks",
         "mapping_strength": "moderate", "evidence_type": "indirect", "confidence": "medium", "manual_review": True},
        {"framework": "NIST SP 800-53", "control_id": "SI-3", "control_name": "Malicious Code Protection",
         "mapping_strength": "weak", "evidence_type": "heuristic", "confidence": "medium", "manual_review": True},
        {"framework": "SOC 2", "control_id": "CC6.1", "control_name": "Logical and Physical Access Controls",
         "mapping_strength": "weak", "evidence_type": "heuristic", "confidence": "medium", "manual_review": True},
    ],
    "AWS_API_GATEWAY_EXPOSED": [
        {"framework": "ISO 27001", "control_id": "A.14.1.2", "control_name": "Securing application services on public networks",
         "mapping_strength": "strong", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "NIST SP 800-53", "control_id": "AC-3", "control_name": "Access Enforcement",
         "mapping_strength": "strong", "evidence_type": "direct", "confidence": "high", "manual_review": False},
        {"framework": "SOC 2", "control_id": "CC6.1", "control_name": "Logical and Physical Access Controls",
         "mapping_strength": "strong", "evidence_type": "direct", "confidence": "high", "manual_review": False},
    ],
    "AWS_ELB_HEADER_DISCLOSURE": [
        {"framework": "ISO 27001", "control_id": "A.12.6.1", "control_name": "Management of technical vulnerabilities",
         "mapping_strength": "weak", "evidence_type": "heuristic", "confidence": "medium", "manual_review": True},
        {"framework": "NIST SP 800-53", "control_id": "SI-11", "control_name": "Error Handling",
         "mapping_strength": "weak", "evidence_type": "heuristic", "confidence": "medium", "manual_review": True},
        {"framework": "SOC 2", "control_id": "CC6.6", "control_name": "Security Event Monitoring",
         "mapping_strength": "weak", "evidence_type": "heuristic", "confidence": "low", "manual_review": True},
    ],
    "AWS_IMDS_EXPOSURE_PATTERN": [
        {"framework": "ISO 27001", "control_id": "A.14.1.2", "control_name": "Securing application services on public networks",
         "mapping_strength": "moderate", "evidence_type": "indirect", "confidence": "medium", "manual_review": True},
        {"framework": "NIST SP 800-53", "control_id": "SI-3", "control_name": "Malicious Code Protection",
         "mapping_strength": "moderate", "evidence_type": "indirect", "confidence": "medium", "manual_review": True},
        {"framework": "SOC 2", "control_id": "CC6.1", "control_name": "Logical and Physical Access Controls",
         "mapping_strength": "moderate", "evidence_type": "indirect", "confidence": "medium", "manual_review": True},
    ],
    "AWS_WAF_ABSENT_SIGNAL": [
        {"framework": "ISO 27001", "control_id": "A.12.6.1", "control_name": "Management of technical vulnerabilities",
         "mapping_strength": "weak", "evidence_type": "heuristic", "confidence": "low", "manual_review": True},
        {"framework": "NIST SP 800-53", "control_id": "SI-3", "control_name": "Malicious Code Protection",
         "mapping_strength": "weak", "evidence_type": "heuristic", "confidence": "low", "manual_review": True},
        {"framework": "SOC 2", "control_id": "CC6.6", "control_name": "Security Event Monitoring",
         "mapping_strength": "weak", "evidence_type": "heuristic", "confidence": "low", "manual_review": True},
    ],
    "AWS_ROUTE53_MISCONFIG_SIGNAL": [
        {"framework": "ISO 27001", "control_id": "A.13.1.1", "control_name": "Network controls",
         "mapping_strength": "weak", "evidence_type": "heuristic", "confidence": "low", "manual_review": True},
        {"framework": "NIST SP 800-53", "control_id": "SC-20", "control_name": "Secure Name / Address Resolution Service",
         "mapping_strength": "weak", "evidence_type": "heuristic", "confidence": "low", "manual_review": True},
        {"framework": "SOC 2", "control_id": "CC6.1", "control_name": "Logical and Physical Access Controls",
         "mapping_strength": "weak", "evidence_type": "heuristic", "confidence": "low", "manual_review": True},
    ],
}


# ── Generic mappings for dynamically-generated finding codes ──

_GENERIC_PORT: list[dict] = [
    {"framework": "ISO 27001", "control_id": "A.13.1.1", "control_name": "Network controls",
     "mapping_strength": "moderate", "evidence_type": "direct", "confidence": "high", "manual_review": False},
    {"framework": "NIST SP 800-53", "control_id": "CM-7", "control_name": "Least Functionality",
     "mapping_strength": "moderate", "evidence_type": "direct", "confidence": "high", "manual_review": False},
    {"framework": "SOC 2", "control_id": "CC6.1", "control_name": "Logical and Physical Access Controls",
     "mapping_strength": "weak", "evidence_type": "indirect", "confidence": "medium", "manual_review": True},
]

_GENERIC_VERSION: list[dict] = [
    {"framework": "ISO 27001", "control_id": "A.12.6.1", "control_name": "Management of technical vulnerabilities",
     "mapping_strength": "weak", "evidence_type": "heuristic", "confidence": "medium", "manual_review": True},
    {"framework": "NIST SP 800-53", "control_id": "SI-2", "control_name": "Flaw Remediation",
     "mapping_strength": "weak", "evidence_type": "heuristic", "confidence": "low", "manual_review": True},
    {"framework": "SOC 2", "control_id": "CC7.1", "control_name": "Detection of Changes",
     "mapping_strength": "weak", "evidence_type": "heuristic", "confidence": "low", "manual_review": True},
]


# ────────────────────────────────────────────
# Control catalogs (used by PDF report)
# ────────────────────────────────────────────
ISO_CONTROLS = {
    "A.10.1.1": "Cryptographic controls – Policy on the use of cryptographic controls",
    "A.10.1.2": "Key management – Key lifecycle management policies",
    "A.12.6.1": "Management of technical vulnerabilities – Timely identification and remediation",
    "A.13.1.1": "Network controls – Networks managed and controlled to protect information",
    "A.14.1.2": "Securing application services – Protecting data over public networks",
    "A.14.1.3": "Protecting application service transactions – Ensuring transaction integrity",
    "A.14.2.5": "Secure system engineering principles – Secure development lifecycle",
    "A.18.1.4": "Privacy and protection of PII – Compliance with privacy legislation",
}

NIST_CONTROLS = {
    "AC-4":  "Information Flow Enforcement – Control information flows between systems",
    "CM-7":  "Least Functionality – Restrict unnecessary functions, ports, protocols",
    "SC-8":  "Transmission Confidentiality and Integrity – Protect data in transit",
    "SC-13": "Cryptographic Protection – Use FIPS-validated cryptography",
    "SC-17": "Public Key Infrastructure Certificates – Issue and manage PKI certs per policy",
    "SC-20": "Secure Name / Address Resolution – Provide authentic and integrity-protected DNS",
    "SC-23": "Session Authenticity – Protect session integrity",
    "SI-2":  "Flaw Remediation – Identify, report, and correct information system flaws",
    "SI-3":  "Malicious Code Protection – Detect and eradicate malicious code",
    "SI-11": "Error Handling – Generate error messages with minimal information disclosure",
}

SOC2_CONTROLS = {
    "CC6.1": "Logical and Physical Access Controls – Restrict access to authorized users",
    "CC6.6": "Security Event Monitoring – Detect anomalies and security events",
    "CC6.7": "Encryption of Data in Transit – Protect data transmitted over networks",
    "CC7.1": "Detection of Changes – Identify and respond to security-relevant changes",
}


# ────────────────────────────────────────────
# Public helpers
# ────────────────────────────────────────────

def get_framework_mappings(code: str) -> list[dict]:
    """Return the rich mapping dicts for a finding code."""
    if code in COMPLIANCE_MAP:
        return COMPLIANCE_MAP[code]
    if code.startswith("OPEN_PORT_"):
        return _GENERIC_PORT
    if code.startswith("SERVICE_VERSION_"):
        return _GENERIC_VERSION
    return []


# Backward-compat shim (used by scanner.py to populate Finding.frameworks)
def get_frameworks(code: str) -> list[str]:
    """Return flat framework strings for a finding code (legacy format)."""
    return [
        f"{m['framework']} – {m['control_id']} ({m['control_name']})"
        for m in get_framework_mappings(code)
    ]


def extract_control_id(framework_str: str) -> str:
    """Extract control ID from a framework string like 'ISO 27001 – A.14.1.2 (...)'."""
    parts = framework_str.split("–")
    if len(parts) >= 2:
        return parts[1].strip().split("(")[0].strip()
    return framework_str
