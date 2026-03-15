import ssl
import socket
import ipaddress
from urllib.parse import urlparse
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx

from models import Finding, FrameworkMapping, AWSSecuritySummary
from mapping import get_frameworks, get_framework_mappings
from scoring import RISK_WEIGHTS, get_aws_risk_label, calculate_priority

# Try to import dnspython for authoritative NS lookups; fallback to socket
try:
    import dns.resolver
    HAS_DNSPYTHON = True
except ImportError:
    HAS_DNSPYTHON = False


# ── Check Status Tracking Helper ──

class CheckStatus:
    """Standardized check status tracking."""
    def __init__(self):
        self.checks = {}
    
    def record(self, check_name: str, status: str, error: str = None):
        """Record check execution status: passed, failed, inconclusive, skipped."""
        self.checks[check_name] = {
            "status": status,
            "error": error[:150] if error else None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def to_dict(self):
        return self.checks


# ── DNS Resolution Helper ──

async def resolve_nameservers(domain: str) -> dict:
    """
    Attempt to resolve NS records for domain.
    Returns: {"status": "passed|failed|inconclusive", "nameservers": [...], "error": "...", "method": "dnspython|socket"}
    """
    result = {
        "status": "inconclusive",
        "nameservers": [],
        "error": None,
        "method": None
    }
    
    # Try dnspython first (more authoritative)
    if HAS_DNSPYTHON:
        try:
            import dns.resolver
            answers = dns.resolver.resolve(domain, 'NS')
            nameservers = [str(rdata).rstrip('.') for rdata in answers]
            result["status"] = "passed"
            result["nameservers"] = nameservers
            result["method"] = "dnspython"
            return result
        except Exception as e:
            result["error"] = str(e)
            result["status"] = "inconclusive"
            # Fall through to socket method
    
    # Fallback: socket.getaddrinfo (less authoritative, won't give NS records)
    try:
        result["method"] = "socket.getaddrinfo"
        # This gives A/AAAA records, not NS records, but useful as fallback signal
        result["status"] = "inconclusive"  # Cannot determine NS with socket
        return result
    except Exception as e:
        result["status"] = "failed"
        result["error"] = str(e)
        return result


# ── Security Headers Config ──

SECURITY_HEADERS = {
    "strict-transport-security": {
        "code": "MISSING_HSTS",
        "title": "Missing Strict-Transport-Security Header",
        "severity": "high",
        "recommendation": "Add 'Strict-Transport-Security: max-age=31536000; includeSubDomains' header to enforce HTTPS.",
    },
    "content-security-policy": {
        "code": "MISSING_CSP",
        "title": "Missing Content-Security-Policy Header",
        "severity": "high",
        "recommendation": "Define a Content-Security-Policy to prevent XSS and data injection attacks.",
    },
    "x-frame-options": {
        "code": "MISSING_X_FRAME_OPTIONS",
        "title": "Missing X-Frame-Options Header",
        "severity": "medium",
        "recommendation": "Add 'X-Frame-Options: DENY' or 'SAMEORIGIN' to prevent clickjacking.",
    },
    "x-content-type-options": {
        "code": "MISSING_X_CONTENT_TYPE_OPTIONS",
        "title": "Missing X-Content-Type-Options Header",
        "severity": "medium",
        "recommendation": "Add 'X-Content-Type-Options: nosniff' to prevent MIME-type sniffing.",
    },
    "referrer-policy": {
        "code": "MISSING_REFERRER_POLICY",
        "title": "Missing Referrer-Policy Header",
        "severity": "low",
        "recommendation": "Add 'Referrer-Policy: strict-origin-when-cross-origin' to control referrer information.",
    },
    "permissions-policy": {
        "code": "MISSING_PERMISSIONS_POLICY",
        "title": "Missing Permissions-Policy Header",
        "severity": "medium",
        "recommendation": "Add a Permissions-Policy header to control browser feature access (camera, mic, geolocation, etc.).",
    },
    "x-xss-protection": {
        "code": "MISSING_X_XSS_PROTECTION",
        "title": "Missing X-XSS-Protection Header",
        "severity": "low",
        "recommendation": "Add 'X-XSS-Protection: 1; mode=block' for legacy browser XSS filtering (supplement CSP).",
    },
}


def _is_safe_target(domain: str) -> bool:
    """Block private IPs, localhost, and other unsafe targets."""
    if domain in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
        return False
    try:
        ip = ipaddress.ip_address(domain)
        if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
            return False
    except ValueError:
        pass
    parts = domain.split(".")
    if len(parts) < 2:
        return False
    if parts[-1] in ("local", "internal", "localhost", "test"):
        return False
    return True


def _normalize_domain(raw: str) -> str:
    """Strip protocol/path — return bare hostname."""
    raw = raw.strip().lower()
    if "://" in raw:
        raw = urlparse(raw).hostname or raw
    raw = raw.split("/")[0].split(":")[0]
    return raw


# ── Check: Security Headers ──

async def check_headers(domain: str) -> tuple[list[Finding], dict]:
    """Fetch the domain over HTTPS, check security headers, and return response metadata."""
    findings: list[Finding] = []
    meta: dict = {}
    url = f"https://{domain}"

    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True, verify=True) as client:
            resp = await client.get(url)
    except Exception:
        return findings, meta

    meta["status_code"] = resp.status_code
    meta["final_url"] = str(resp.url)
    meta["server"] = resp.headers.get("server", "Unknown")
    meta["redirect_chain"] = [str(r.url) for r in resp.history] if resp.history else []
    # CRITICAL FIX: Include full headers dict for dependent checks (CloudFront, WAF, etc.)
    meta["headers"] = dict(resp.headers)

    headers_lower = {k.lower(): v for k, v in resp.headers.items()}

    for header_name, info in SECURITY_HEADERS.items():
        if header_name not in headers_lower:
            _code = info["code"]
            findings.append(
                Finding(
                    code=_code,
                    title=info["title"],
                    severity=info["severity"],
                    confidence="high",  # Missing headers are high-confidence findings
                    check_status="passed",
                    evidence=f"Header '{header_name}' was not found in the response from {meta['final_url']} (HTTP {meta['status_code']})",
                    recommendation=info["recommendation"],
                    frameworks=get_frameworks(_code),
                    framework_mappings=[FrameworkMapping(**m) for m in get_framework_mappings(_code)],
                )
            )

    # ── Weak HSTS check ──
    hsts_val = headers_lower.get("strict-transport-security", "")
    if hsts_val:
        try:
            max_age = int([p.split("=")[1] for p in hsts_val.split(";") if "max-age" in p.lower()][0])
            if max_age < 15768000:  # less than 6 months
                findings.append(
                    Finding(
                        code="WEAK_HSTS",
                        title="Weak HSTS max-age Value",
                        severity="medium",
                        confidence="high",
                        check_status="passed",
                        confidence_reason="HSTS header is present but max-age value is directly parseable and verifiably weak",
                        evidence=f"HSTS max-age is {max_age}s (< 6 months). Value: '{hsts_val}'",
                        recommendation="Set max-age to at least 31536000 (1 year). Consider adding includeSubDomains and preload.",
                        frameworks=get_frameworks("WEAK_HSTS"),
                        framework_mappings=[FrameworkMapping(**m) for m in get_framework_mappings("WEAK_HSTS")],
                    )
                )
        except (IndexError, ValueError):
            pass

    # ── Cookie security check ──
    for cookie_header in resp.headers.get_list("set-cookie"):
        cookie_lower = cookie_header.lower()
        cookie_name = cookie_header.split("=")[0].strip()
        issues = []
        if "secure" not in cookie_lower:
            issues.append("Secure flag missing")
        if "httponly" not in cookie_lower:
            issues.append("HttpOnly flag missing")
        if "samesite" not in cookie_lower:
            issues.append("SameSite attribute missing")
        if issues:
            findings.append(
                Finding(
                    code="INSECURE_COOKIE",
                    title=f"Insecure Cookie: {cookie_name}",
                    severity="medium",
                    confidence="high",
                    check_status="passed",
                    confidence_reason="Set-Cookie header is directly observable and analyzable",
                    evidence=f"Cookie '{cookie_name}' issues: {', '.join(issues)}. Raw: {cookie_header[:120]}",
                    recommendation="Set Secure, HttpOnly, and SameSite=Strict (or Lax) on all cookies.",
                    frameworks=get_frameworks("INSECURE_COOKIE"),
                    framework_mappings=[FrameworkMapping(**m) for m in get_framework_mappings("INSECURE_COOKIE")],
                )
            )

    # ── Information disclosure: Server header ──
    server_val = headers_lower.get("server", "")
    if server_val and any(v in server_val.lower() for v in ("/", ".", "apache", "nginx", "iis", "php")):
        findings.append(
            Finding(
                code="SERVER_INFO_DISCLOSURE",
                title="Server Version Information Disclosure",
                severity="low",
                confidence="high",
                check_status="passed",
                confidence_reason="Server header is directly observable in HTTP response",
                evidence=f"Server header reveals: '{server_val}'",
                recommendation="Remove or minimize the Server header to avoid leaking software version information.",
                frameworks=get_frameworks("SERVER_INFO_DISCLOSURE"),
                framework_mappings=[FrameworkMapping(**m) for m in get_framework_mappings("SERVER_INFO_DISCLOSURE")],
            )
        )

    # ── X-Powered-By disclosure ──
    powered = headers_lower.get("x-powered-by", "")
    if powered:
        findings.append(
            Finding(
                code="X_POWERED_BY_DISCLOSURE",
                title="X-Powered-By Information Disclosure",
                severity="low",
                confidence="high",
                check_status="passed",
                confidence_reason="X-Powered-By header is directly observable in HTTP response",
                evidence=f"X-Powered-By header reveals: '{powered}'",
                recommendation="Remove the X-Powered-By header to prevent technology fingerprinting.",
                frameworks=get_frameworks("X_POWERED_BY_DISCLOSURE"),
                framework_mappings=[FrameworkMapping(**m) for m in get_framework_mappings("X_POWERED_BY_DISCLOSURE")],
            )
        )

    return findings, meta


# ── Check: TLS / Certificate ──

def check_tls(domain: str) -> tuple[list[Finding], dict]:
    """TLS connection + certificate analysis. Returns findings and TLS metadata."""
    findings: list[Finding] = []
    tls_meta: dict = {}

    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                tls_meta["protocol"] = ssock.version()
                cert = ssock.getpeercert()

                # Extract cert details
                tls_meta["subject"] = dict(x[0] for x in cert.get("subject", ()))
                tls_meta["issuer"] = dict(x[0] for x in cert.get("issuer", ()))
                tls_meta["serial"] = cert.get("serialNumber", "N/A")
                tls_meta["not_before"] = cert.get("notBefore", "")
                tls_meta["not_after"] = cert.get("notAfter", "")
                tls_meta["san"] = [v for _, v in cert.get("subjectAltName", ())]

                # Check for weak TLS version
                ver = ssock.version() or ""
                if ver in ("TLSv1", "TLSv1.1", "SSLv3", "SSLv2"):
                    findings.append(
                        Finding(
                            code="WEAK_TLS_VERSION",
                            title=f"Weak TLS Version: {ver}",
                            severity="high",
                            confidence="high",
                            check_status="passed",
                            confidence_reason="TLS version directly negotiated during handshake and verified",
                            evidence=f"Server negotiated {ver} which is deprecated and insecure.",
                            recommendation="Disable TLS 1.0, TLS 1.1, SSLv3. Support only TLS 1.2+.",
                            frameworks=get_frameworks("WEAK_TLS_VERSION"),
                            framework_mappings=[FrameworkMapping(**m) for m in get_framework_mappings("WEAK_TLS_VERSION")],
                        )
                    )

                # Certificate expiration check
                not_after_str = cert.get("notAfter", "")
                if not_after_str:
                    expiry = datetime.strptime(not_after_str, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
                    days_left = (expiry - datetime.now(timezone.utc)).days
                    tls_meta["days_until_expiry"] = days_left

                    if days_left < 0:
                        findings.append(
                            Finding(
                                code="CERT_EXPIRED",
                                title="SSL Certificate Expired",
                                severity="critical",
                                confidence="high",
                                check_status="passed",
                                confidence_reason="Certificate expiry date is directly readable from X.509 cert structure",
                                evidence=f"Certificate expired {abs(days_left)} days ago (expired: {not_after_str}).",
                                recommendation="Renew the SSL certificate immediately.",
                                frameworks=get_frameworks("CERT_EXPIRED"),
                                framework_mappings=[FrameworkMapping(**m) for m in get_framework_mappings("CERT_EXPIRED")],
                            )
                        )
                    elif days_left < 30:
                        findings.append(
                            Finding(
                                code="CERT_EXPIRING_SOON",
                                title="SSL Certificate Expiring Soon",
                                severity="high",
                                confidence="high",
                                check_status="passed",
                                confidence_reason="Certificate expiry date is directly readable from X.509 cert structure",
                                evidence=f"Certificate expires in {days_left} days (on {not_after_str}).",
                                recommendation="Renew the SSL certificate before it expires.",
                                frameworks=get_frameworks("CERT_EXPIRING_SOON"),
                                framework_mappings=[FrameworkMapping(**m) for m in get_framework_mappings("CERT_EXPIRING_SOON")],
                            )
                        )

                # Self-signed check (issuer == subject)
                subj = tls_meta.get("subject", {})
                iss = tls_meta.get("issuer", {})
                if subj and subj == iss:
                    findings.append(
                        Finding(
                            code="SELF_SIGNED_CERT",
                            title="Self-Signed Certificate Detected",
                            severity="high",
                            confidence="high",
                            check_status="passed",
                            confidence_reason="Subject and issuer fields directly compared from X.509 cert",
                            evidence=f"Certificate issuer matches subject: '{iss.get('organizationName', iss.get('commonName', 'N/A'))}'",
                            recommendation="Use a certificate from a trusted Certificate Authority (CA).",
                            frameworks=get_frameworks("SELF_SIGNED_CERT"),
                            framework_mappings=[FrameworkMapping(**m) for m in get_framework_mappings("SELF_SIGNED_CERT")],
                        )
                    )

    except ssl.SSLCertVerificationError as exc:
        tls_meta["error"] = str(exc)
        findings.append(
            Finding(
                code="TLS_CERT_INVALID",
                title="TLS Certificate Verification Failed",
                severity="critical",
                confidence="high",
                check_status="passed",
                confidence_reason="TLS verification error raised by standard library SSL module during handshake",
                evidence=f"Certificate verification failed for {domain}:443 — {exc}",
                recommendation="Fix the certificate issue: ensure it's valid, not expired, and issued by a trusted CA.",
                frameworks=get_frameworks("TLS_CERT_INVALID"),
                framework_mappings=[FrameworkMapping(**m) for m in get_framework_mappings("TLS_CERT_INVALID")],
            )
        )
    except Exception as exc:
        tls_meta["error"] = str(exc)
        findings.append(
            Finding(
                code="TLS_FAILURE",
                title="TLS Connection Failure",
                severity="critical",
                confidence="high",
                check_status="passed",
                confidence_reason="TLS connection exception raised during handshake attempt",
                evidence=f"Could not establish a TLS connection to {domain}:443 — {exc}",
                recommendation="Ensure the server supports TLS 1.2+ and has a valid certificate.",
                frameworks=get_frameworks("TLS_FAILURE"),
                framework_mappings=[FrameworkMapping(**m) for m in get_framework_mappings("TLS_FAILURE")],
            )
        )

    return findings, tls_meta


# ── Check: HTTP → HTTPS redirect ──

async def check_https_redirect(domain: str) -> list[Finding]:
    """Check if HTTP automatically redirects to HTTPS."""
    findings: list[Finding] = []
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=False, verify=True) as client:
            resp = await client.get(f"http://{domain}")
        if resp.status_code not in (301, 302, 307, 308):
            findings.append(
                Finding(
                    code="NO_HTTPS_REDIRECT",
                    title="No HTTP to HTTPS Redirect",
                    severity="high",
                    evidence=f"http://{domain} returned HTTP {resp.status_code} instead of a redirect to HTTPS.",
                    recommendation="Configure the server to redirect all HTTP traffic to HTTPS with a 301 redirect.",
                    frameworks=get_frameworks("NO_HTTPS_REDIRECT"),
                    framework_mappings=[FrameworkMapping(**m) for m in get_framework_mappings("NO_HTTPS_REDIRECT")],
                )
            )
        else:
            location = resp.headers.get("location", "")
            if location and not location.lower().startswith("https://"):
                findings.append(
                    Finding(
                        code="REDIRECT_NOT_HTTPS",
                        title="HTTP Redirect Does Not Point to HTTPS",
                        severity="medium",
                        evidence=f"http://{domain} redirects to '{location}' which is not HTTPS.",
                        recommendation="Ensure the redirect location uses https://.",
                        frameworks=get_frameworks("REDIRECT_NOT_HTTPS"),
                        framework_mappings=[FrameworkMapping(**m) for m in get_framework_mappings("REDIRECT_NOT_HTTPS")],
                    )
                )
    except Exception:
        pass  # If HTTP doesn't respond at all, not necessarily a problem
    return findings


# ── Check: Open ports ──

# Full port catalog: port → (service_name, is_risky, severity)
PORT_CATALOG: dict[int, tuple[str, bool, str]] = {
    # Web & proxy
    80:    ("HTTP", False, "info"),
    443:   ("HTTPS", False, "info"),
    8080:  ("HTTP-Alt / Proxy", False, "low"),
    8443:  ("HTTPS-Alt", False, "info"),
    8888:  ("HTTP-Alt", False, "low"),
    3128:  ("Squid Proxy", True, "medium"),
    # Mail
    25:    ("SMTP", True, "medium"),
    465:   ("SMTPS", False, "info"),
    587:   ("SMTP Submission", False, "info"),
    110:   ("POP3", True, "medium"),
    143:   ("IMAP", True, "medium"),
    993:   ("IMAPS", False, "info"),
    995:   ("POP3S", False, "info"),
    # File transfer
    21:    ("FTP", True, "high"),
    22:    ("SSH", False, "info"),
    69:    ("TFTP", True, "high"),
    # Remote access
    23:    ("Telnet", True, "critical"),
    3389:  ("RDP", True, "critical"),
    5900:  ("VNC", True, "critical"),
    5901:  ("VNC-1", True, "critical"),
    # Databases
    1433:  ("MSSQL", True, "critical"),
    1521:  ("Oracle DB", True, "critical"),
    3306:  ("MySQL", True, "critical"),
    5432:  ("PostgreSQL", True, "critical"),
    6379:  ("Redis", True, "critical"),
    9200:  ("Elasticsearch", True, "critical"),
    27017: ("MongoDB", True, "critical"),
    5984:  ("CouchDB", True, "critical"),
    # Message queues & cache
    11211: ("Memcached", True, "high"),
    5672:  ("RabbitMQ", True, "high"),
    9092:  ("Kafka", True, "high"),
    # Misc services
    53:    ("DNS", False, "info"),
    111:   ("RPCbind", True, "high"),
    135:   ("MS-RPC", True, "high"),
    139:   ("NetBIOS", True, "high"),
    445:   ("SMB", True, "critical"),
    161:   ("SNMP", True, "high"),
    389:   ("LDAP", True, "high"),
    636:   ("LDAPS", False, "info"),
    873:   ("Rsync", True, "medium"),
    2049:  ("NFS", True, "high"),
    8081:  ("HTTP-Alt-2", False, "low"),
    9090:  ("Management Console", True, "medium"),
    10000: ("Webmin", True, "high"),
}


# Probes sent to coax a banner out of common services
_PROBE_MAP: dict[int, bytes] = {
    80:   b"HEAD / HTTP/1.0\r\nHost: probe\r\n\r\n",
    8080: b"HEAD / HTTP/1.0\r\nHost: probe\r\n\r\n",
    8443: b"HEAD / HTTP/1.0\r\nHost: probe\r\n\r\n",
    8888: b"HEAD / HTTP/1.0\r\nHost: probe\r\n\r\n",
    8081: b"HEAD / HTTP/1.0\r\nHost: probe\r\n\r\n",
    9090: b"HEAD / HTTP/1.0\r\nHost: probe\r\n\r\n",
    3128: b"HEAD / HTTP/1.0\r\nHost: probe\r\n\r\n",
    10000: b"HEAD / HTTP/1.0\r\nHost: probe\r\n\r\n",
    9200: b"GET / HTTP/1.0\r\n\r\n",
    5984: b"GET / HTTP/1.0\r\n\r\n",
}


def _grab_banner(sock: socket.socket, port: int, timeout: float = 3.0) -> str:
    """Try to read a service banner from an open socket."""
    try:
        sock.settimeout(timeout)
        # Some services send a banner immediately; others need a probe
        probe = _PROBE_MAP.get(port)
        if probe:
            sock.sendall(probe)
        else:
            # For services that don't get a probe, try reading first,
            # then send a generic probe if nothing comes back
            pass

        data = b""
        try:
            data = sock.recv(1024)
        except socket.timeout:
            pass

        if not data and not probe:
            # Send a generic nudge
            try:
                sock.sendall(b"\r\n")
                sock.settimeout(2.0)
                data = sock.recv(1024)
            except (socket.timeout, OSError):
                pass

        if data:
            # Decode and clean up — take first meaningful line
            text = data.decode("utf-8", errors="replace").strip()
            # For HTTP responses, extract the Server header
            if text.upper().startswith("HTTP/"):
                for line in text.split("\r\n"):
                    if line.lower().startswith("server:"):
                        return line.split(":", 1)[1].strip()[:120]
                # Fallback: return the status line
                return text.split("\r\n")[0][:120]
            # For other protocols, return first line
            first_line = text.split("\n")[0].split("\r")[0][:120]
            return first_line
    except Exception:
        pass
    return ""


def _scan_single_port(domain: str, port: int, timeout: float = 2.0) -> tuple[int, bool, str]:
    """Try connecting to a single port. Returns (port, is_open, banner)."""
    try:
        sock = socket.create_connection((domain, port), timeout=timeout)
        banner = _grab_banner(sock, port)
        try:
            sock.close()
        except OSError:
            pass
        return (port, True, banner)
    except (socket.timeout, ConnectionRefusedError, OSError):
        return (port, False, "")


def check_ports(domain: str) -> tuple[list[Finding], dict]:
    """Scan all ports in PORT_CATALOG concurrently. Returns findings and port metadata."""
    findings: list[Finding] = []
    open_ports: list[dict] = []
    closed_count = 0

    with ThreadPoolExecutor(max_workers=40) as pool:
        futures = {
            pool.submit(_scan_single_port, domain, port): port
            for port in PORT_CATALOG
        }
        for future in as_completed(futures):
            port, is_open, banner = future.result()
            service, is_risky, severity = PORT_CATALOG[port]
            if is_open:
                open_ports.append({
                    "port": port,
                    "service": service,
                    "banner": banner,
                    "risky": is_risky,
                    "severity": severity,
                })
                if is_risky:
                    _pcode = f"OPEN_PORT_{port}"
                    version_info = f" Banner: '{banner}'" if banner else ""
                    findings.append(
                        Finding(
                            code=_pcode,
                            title=f"Risky Open Port: {port}/{service}",
                            severity=severity,
                            evidence=f"Port {port} ({service}) is open and accepting connections on {domain}.{version_info} This service should not be publicly exposed.",
                            recommendation=f"Close port {port} or restrict access via firewall rules. {service} should not be publicly accessible.",
                            frameworks=get_frameworks(_pcode),
                            framework_mappings=[FrameworkMapping(**m) for m in get_framework_mappings(_pcode)],
                        )
                    )
                # Version disclosure finding for any port with a detailed banner
                if banner and any(c.isdigit() for c in banner):
                    _vcode = f"SERVICE_VERSION_{port}"
                    findings.append(
                        Finding(
                            code=_vcode,
                            title=f"Service Version Disclosure on Port {port}",
                            severity="low",
                            evidence=f"Port {port} ({service}) reveals version info: '{banner}'",
                            recommendation=f"Suppress or minimize the banner on port {port} to prevent fingerprinting.",
                            frameworks=get_frameworks(_vcode),
                            framework_mappings=[FrameworkMapping(**m) for m in get_framework_mappings(_vcode)],
                        )
                    )
            else:
                closed_count += 1

    # Sort open ports by port number
    open_ports.sort(key=lambda p: p["port"])

    port_meta = {
        "total_scanned": len(PORT_CATALOG),
        "open_count": len(open_ports),
        "closed_count": closed_count,
        "open_ports": open_ports,
    }

    return findings, port_meta


# ── Check: DNS configuration ──

def check_dns(domain: str) -> tuple[list[Finding], dict]:
    """Resolve domain and collect DNS metadata."""
    findings: list[Finding] = []
    dns_meta: dict = {}
    try:
        addrs = socket.getaddrinfo(domain, None)
        ips = sorted(set(addr[4][0] for addr in addrs))
        dns_meta["resolved_ips"] = ips
    except socket.gaierror as exc:
        dns_meta["error"] = str(exc)
        findings.append(
            Finding(
                code="DNS_RESOLUTION_FAILURE",
                title="DNS Resolution Failed",
                severity="critical",
                evidence=f"Could not resolve {domain}: {exc}",
                recommendation="Check that the domain's DNS records are properly configured.",
                frameworks=get_frameworks("DNS_RESOLUTION_FAILURE"),
                framework_mappings=[FrameworkMapping(**m) for m in get_framework_mappings("DNS_RESOLUTION_FAILURE")],
            )
        )
    return findings, dns_meta


# ── Main scan orchestrator ──

async def scan_domain(raw_input: str) -> tuple[list[Finding], dict]:
    """Run all checks with structured error tracking. Returns (findings, scan_meta). Raises ValueError for unsafe targets."""
    domain = _normalize_domain(raw_input)

    if not domain or not _is_safe_target(domain):
        raise ValueError(
            f"'{raw_input}' is not allowed. Private IPs, localhost, and internal hostnames are blocked."
        )

    scan_meta: dict = {"domain": domain, "scan_time": datetime.now(timezone.utc).isoformat()}
    check_status = CheckStatus()

    # DNS
    try:
        dns_findings, dns_meta = check_dns(domain)
        scan_meta["dns"] = dns_meta
        check_status.record("dns", "passed" if not dns_findings else "passed_with_findings")
        if dns_findings:
            # If DNS fails, no point continuing
            scan_meta["tls"] = {}
            scan_meta["http"] = {}
            check_status.record("tls", "skipped")
            check_status.record("headers", "skipped")
            check_status.record("redirect", "skipped")
            check_status.record("ports", "skipped")
            check_status.record("aws", "skipped")
    except Exception as e:
        check_status.record("dns", "failed", str(e))
        scan_meta["dns_error"] = str(e)[:150]
        scan_meta["dns"] = {}
        scan_meta["tls"] = {}
        scan_meta["http"] = {}
        return [], scan_meta

    # TLS / Certificate
    try:
        tls_findings, tls_meta = check_tls(domain)
        scan_meta["tls"] = tls_meta
        check_status.record("tls", "passed")
    except Exception as e:
        check_status.record("tls", "failed", str(e))
        scan_meta["tls_error"] = str(e)[:150]

    # HTTP headers
    try:
        header_findings, http_meta = await check_headers(domain)
        scan_meta["http"] = http_meta
        check_status.record("headers", "passed")
    except Exception as e:
        check_status.record("headers", "failed", str(e))
        scan_meta["http_error"] = str(e)[:150]
        header_findings = []
        http_meta = {}

    # HTTPS redirect
    try:
        redirect_findings = await check_https_redirect(domain)
        check_status.record("redirect", "passed")
    except Exception as e:
        check_status.record("redirect", "failed", str(e))
        redirect_findings = []

    # Open ports (concurrent)
    try:
        port_findings, port_meta = check_ports(domain)
        scan_meta["ports"] = port_meta
        check_status.record("ports", "passed")
    except Exception as e:
        check_status.record("ports", "failed", str(e))
        port_findings = []

    # AWS Security Checks
    try:
        aws_findings, aws_meta = await check_aws(domain, http_meta, dns_meta)
        scan_meta["aws"] = aws_meta
        check_status.record("aws", "passed")
    except Exception as e:
        check_status.record("aws", "failed", str(e))
        scan_meta["aws_error"] = str(e)[:150]
        aws_findings = []

    all_findings = dns_findings + tls_findings + header_findings + redirect_findings + port_findings + aws_findings

    # Sort by severity
    sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    all_findings.sort(key=lambda f: sev_order.get(f.severity, 5))

    # Add checks summary to metadata
    scan_meta["checks_summary"] = check_status.to_dict()

    # Build AWS summary (transparent breakdown available in scan_meta)
    aws_findings_list = [f for f in all_findings if f.code.startswith("AWS_")]
    aws_score_contribution = sum(RISK_WEIGHTS.get(f.code, 8) for f in aws_findings_list)
    aws_services = aws_meta.get("aws_services_detected", [])
    
    aws_summary = AWSSecuritySummary(
        aws_findings_count=len(aws_findings_list),
        aws_score_contribution=aws_score_contribution,
        aws_services_detected=aws_services,
        aws_risk_label=get_aws_risk_label(aws_score_contribution),
        aws_findings=aws_findings_list,
    )
    scan_meta["aws_summary"] = aws_summary.model_dump()

    return all_findings, scan_meta


# ── AWS Security Checks ──

def _detect_aws_service_patterns(domain: str) -> list[str]:
    """Detect AWS service patterns from domain name."""
    services = []
    domain_lower = domain.lower()
    
    if "cloudfront" in domain_lower or ".cf.amplifyapp.com" in domain_lower:
        services.append("CloudFront")
    if "elb" in domain_lower or "elasticloadbalanc" in domain_lower:
        services.append("ELB")
    if "execute-api" in domain_lower:
        services.append("API Gateway")
    if "s3" in domain_lower or ".s3" in domain_lower or "s3-" in domain_lower:
        services.append("S3")
    if "route53" in domain_lower or ".awsdns-" in domain_lower:
        services.append("Route53")
    
    return services


async def check_aws_s3(domain: str) -> tuple[list[Finding], dict]:
    """Check for S3 public bucket exposure with structured error tracking."""
    findings: list[Finding] = []
    meta: dict = {
        "s3_check_status": "skipped",
        "s3_errors": []
    }
    
    # Try common S3 variations (virtual-hosted and path-style)
    s3_variations = [
        f"{domain}.s3.amazonaws.com",
        f"{domain}.s3-website.amazonaws.com",
        f"{domain}-static.s3.amazonaws.com",
        f"s3.{domain}",
    ]
    
    bucket_tested = False
    for s3_host in s3_variations:
        try:
            async with httpx.AsyncClient(timeout=5, verify=True) as client:
                # HEAD request to check if bucket exists
                try:
                    head_resp = await client.head(f"https://{s3_host}", follow_redirects=False, timeout=5)
                except Exception as e:
                    meta["s3_errors"].append({"endpoint": s3_host, "step": "HEAD", "error": str(e)[:100]})
                    continue
                
                if head_resp.status_code not in (200, 301, 302, 307, 403, 404):
                    continue  # Not a valid S3 endpoint
                
                bucket_tested = True
                meta["s3_detected"] = True
                meta["s3_endpoint"] = s3_host
                meta["s3_check_status"] = "passed"
                
                # Try LIST operation (GET with ?max-keys=0)
                try:
                    list_resp = await client.get(f"https://{s3_host}/?max-keys=0", timeout=3, follow_redirects=False)
                    if list_resp.status_code == 200:
                        # Check if response contains ListBucketResult XML
                        if b"ListBucketResult" in list_resp.content or b"<Contents>" in list_resp.content:
                            findings.append(
                                Finding(
                                    code="AWS_S3_BUCKET_ENUMERABLE",
                                    title="AWS S3 Bucket Allows Public Listing",
                                    severity="high",
                                    confidence="high",
                                    check_status="passed",
                                    confidence_reason="ListBucketResult XML returned in HTTP 200 response, proving public enumeration access",
                                    evidence=f"S3 bucket at {s3_host} allows public bucket enumeration. HTTP {list_resp.status_code} with ListBucketResult XML returned. Bucket contents can be listed by unauthenticated users.",
                                    recommendation="Disable public 's3:ListBucket' permission on the S3 bucket. Restrict bucket policy to deny anonymous 'List' actions. Enable S3 Block Public Access.",
                                    frameworks=get_frameworks("AWS_S3_BUCKET_ENUMERABLE"),
                                    framework_mappings=[FrameworkMapping(**m) for m in get_framework_mappings("AWS_S3_BUCKET_ENUMERABLE")],
                                )
                            )
                        else:
                            # Status 200 without explicit ListBucketResult also indicates public list
                            findings.append(
                                Finding(
                                    code="AWS_S3_BUCKET_ENUMERABLE",
                                    title="AWS S3 Bucket Allows Public Listing",
                                    severity="high",
                                    confidence="high",
                                    check_status="passed",
                                    confidence_reason="HTTP 200 without AccessDenied error indicates bucket enumeration permission",
                                    evidence=f"S3 bucket at {s3_host} allows public bucket enumeration (HTTP {list_resp.status_code}, no AccessDenied response).",
                                    recommendation="Disable public 's3:ListBucket' permission on the S3 bucket. Restrict bucket policy to deny anonymous 'List' actions. Enable S3 Block Public Access.",
                                    frameworks=get_frameworks("AWS_S3_BUCKET_ENUMERABLE"),
                                    framework_mappings=[FrameworkMapping(**m) for m in get_framework_mappings("AWS_S3_BUCKET_ENUMERABLE")],
                                )
                            )
                except httpx.TimeoutException as e:
                    meta["s3_errors"].append({"endpoint": s3_host, "step": "LIST", "error_type": "timeout", "error": str(e)[:100]})
                    meta["s3_check_status"] = "inconclusive"
                except Exception as e:
                    meta["s3_errors"].append({"endpoint": s3_host, "step": "LIST", "error_type": type(e).__name__, "error": str(e)[:100]})
                    meta["s3_check_status"] = "inconclusive"
                
                break  # Got response from this endpoint, stop trying others
        except Exception as e:
            meta["s3_errors"].append({"endpoint": s3_host, "step": "initial_connect", "error_type": type(e).__name__, "error": str(e)[:100]})
    
    if not bucket_tested:
        meta["s3_check_status"] = "inconclusive"
    
    return findings, meta


async def check_aws_cloudfront(domain: str, http_meta: dict) -> list[Finding]:
    """Check CloudFront security configuration (cache headers & security practices)."""
    findings: list[Finding] = []
    
    # CloudFront detection: domain pattern OR response headers indicate CloudFront
    is_cloudfront_domain = "cloudfront" in domain.lower() or "cf.amplifyapp.com" in domain.lower()
    
    # Check response headers for CloudFront signatures
    headers_lower = {k.lower(): v for k, v in http_meta.get("headers", {}).items()}
    server_header = headers_lower.get("server", "").lower()
    via_header = headers_lower.get("via", "").lower()
    x_cache_header = headers_lower.get("x-cache", "").lower()
    x_amz_cf_header = headers_lower.get("x-amz-cf-id", "")
    
    is_cloudfront_via_headers = (
        "cloudfront" in via_header or 
        "cloudfront" in x_cache_header or 
        x_amz_cf_header or
        "cloudfront" in server_header
    )
    
    # Only proceed if CloudFront is actually detected
    if not (is_cloudfront_domain or is_cloudfront_via_headers):
        return findings
    
    # CloudFront detected: validate cache security headers
    cache_control = headers_lower.get("cache-control", "")
    expires = headers_lower.get("expires", "")
    pragma = headers_lower.get("pragma", "")
    
    # Check for weak cache configuration
    if not cache_control and not expires and not pragma:
        # No caching directive at all - could be public cacheable
        findings.append(
            Finding(
                code="AWS_CLOUDFRONT_SECURITY_WEAKNESS",
                title="AWS CloudFront Missing Cache Control Headers",
                severity="medium",
                confidence="medium",
                check_status="passed",
                manual_review=True,
                confidence_reason="CloudFront detected via domain/headers but missing cache headers could indicate weak default config; requires manual verification of actual distribution settings",
                evidence=f"CloudFront distribution detected ({domain}) lacks Cache-Control, Expires, or Pragma headers. This may allow sensitive content to be cached in edge locations.",
                recommendation="Configure CloudFront cache behaviors with appropriate Cache-Control directives (e.g., 'must-revalidate, max-age=3600, private'). Use 'no-cache' or 'no-store' for sensitive responses.",
                frameworks=get_frameworks("AWS_CLOUDFRONT_SECURITY_WEAKNESS"),
                framework_mappings=[FrameworkMapping(**m) for m in get_framework_mappings("AWS_CLOUDFRONT_SECURITY_WEAKNESS")],
            )
        )
    elif cache_control and ("public" in cache_control.lower() or "max-age" in cache_control.lower()):
        # Explicitly public or has long cache - warn if sensitive data could be cached
        if "private" not in cache_control.lower():
            findings.append(
                Finding(
                    code="AWS_CLOUDFRONT_SECURITY_WEAKNESS",
                    title="AWS CloudFront Potentially Insecure Cache Behavior",
                    severity="medium",
                    confidence="medium",
                    check_status="passed",
                    manual_review=True,
                    confidence_reason="Cache-Control header is directly observable but actual content type/sensitivity requires application context review",
                    evidence=f"CloudFront distribution ({domain}) has Cache-Control: {cache_control}, which is not marked as 'private'. Shared caches (CDN) may retain sensitive content.",
                    recommendation="Use 'Cache-Control: private, max-age=...' or 'no-store' for sensitive responses. Avoid caching user-specific or sensitive data in CloudFront.",
                    frameworks=get_frameworks("AWS_CLOUDFRONT_SECURITY_WEAKNESS"),
                    framework_mappings=[FrameworkMapping(**m) for m in get_framework_mappings("AWS_CLOUDFRONT_SECURITY_WEAKNESS")],
                )
            )
    
    return findings


async def check_aws_api_gateway(domain: str) -> tuple[list[Finding], dict]:
    """Check for exposed API Gateway endpoints with structured error tracking."""
    findings: list[Finding] = []
    meta: dict = {
        "api_gateway_check_status": "skipped"
    }
    
    if "execute-api" in domain.lower():
        meta["api_gateway_detected"] = True
        meta["api_gateway_check_status"] = "inconclusive"
        
        # Check for unauthenticated public access
        # Note: 403 = auth is working (access denied). 200 or 401 = potential exposure.
        try:
            async with httpx.AsyncClient(timeout=5, verify=True) as client:
                try:
                    resp = await client.get(f"https://{domain}/", follow_redirects=False, timeout=5)
                    meta["api_gateway_check_status"] = "passed"
                except httpx.TimeoutException:
                    meta["api_gateway_error"] = "timeout"
                    meta["api_gateway_check_status"] = "inconclusive"
                    return findings, meta
                except Exception as e:
                    meta["api_gateway_error"] = str(e)[:100]
                    meta["api_gateway_check_status"] = "inconclusive"
                    return findings, meta
                
                # Check for API Gateway response headers
                headers_lower = {k.lower(): v for k, v in resp.headers.items()}
                
                # Exposed finding: GET /  returns 200 (public)
                if resp.status_code == 200:
                    finding_evidence = f"API Gateway endpoint ({domain}) HTTP {resp.status_code} returns data without authentication. Endpoint is publicly accessible. Response headers: {dict(headers_lower)}"
                    findings.append(
                        Finding(
                            code="AWS_API_GATEWAY_EXPOSED",
                            title="AWS API Gateway Publicly Accessible Endpoint",
                            severity="high",
                            confidence="high",
                            check_status="passed",
                            confidence_reason="execute-api domain pattern combined with HTTP 200 without authentication headers indicates public exposure",
                            evidence=finding_evidence,
                            recommendation="Implement AWS API Gateway authorization using API keys, Lambda authorizers (custom logic), Cognito, or IAM policies. Restrict to authorized clients only. Enable request validation and rate limiting.",
                            frameworks=get_frameworks("AWS_API_GATEWAY_EXPOSED"),
                            framework_mappings=[FrameworkMapping(**m) for m in get_framework_mappings("AWS_API_GATEWAY_EXPOSED")],
                        )
                    )
                # 403 = Forbidden (auth is likely working, access denied) - NOT exposed
                # 404 = Endpoint doesn't exist - NOT exposed
        except Exception as e:
            meta["api_gateway_outer_error"] = str(e)[:100]
            meta["api_gateway_check_status"] = "inconclusive"
    
    return findings, meta


async def check_aws_elb(http_meta: dict) -> list[Finding]:
    """Check ELB information disclosure."""
    findings: list[Finding] = []
    
    server_header = http_meta.get("server", "").lower()
    
    if "elb" in server_header or "elasticloadbalanc" in server_header:
        findings.append(
            Finding(
                code="AWS_ELB_HEADER_DISCLOSURE",
                title="AWS Elastic Load Balancer Version Disclosure",
                severity="low",
                confidence="high",
                check_status="passed",
                confidence_reason="ELB string directly observable in Server header",
                evidence=f"Server header reveals ELB version information: '{http_meta.get('server', '')}'",
                recommendation="Configure ELB to suppress or hide the Server header using security group rules or custom headers.",
                frameworks=get_frameworks("AWS_ELB_HEADER_DISCLOSURE"),
                framework_mappings=[FrameworkMapping(**m) for m in get_framework_mappings("AWS_ELB_HEADER_DISCLOSURE")],
            )
        )
    
    return findings


async def check_aws_imds(domain: str) -> list[Finding]:
    """Check for IMDS exposure patterns (non-intrusive heuristic only)."""
    findings: list[Finding] = []
    
    # Non-intrusive IMDS check: Look for patterns in responses that suggest IMDS exposure.
    # We DO NOT attempt path traversal, file reads, or any exploits.
    
    try:
        # Non-intrusive: check if responses contain metadata service indicators
        # Use verify=True (TLS validation required) for security
        async with httpx.AsyncClient(timeout=5, verify=True) as client:
            resp = await client.get(f"https://{domain}/", follow_redirects=False, timeout=3)
            response_text = resp.text.lower()
            
            # Look for AWS credential hints in error messages
            imds_indicators = [
                "aws_access_key", "aws_secret_key", "x-amz-instance-identity",
                "temporary security credentials", "ec2 instance metadata"
            ]
            
            if any(indicator in response_text for indicator in imds_indicators):
                findings.append(
                    Finding(
                        code="AWS_IMDS_EXPOSURE_PATTERN",
                        title="Potential AWS EC2 Metadata Service Exposure Indicator",
                        severity="high",
                        confidence="low",
                        check_status="passed",
                        manual_review=True,
                        confidence_reason="Heuristic keyword matching in response; high false positive risk without manual verification",
                        evidence=f"Domain ({domain}) HTTP response contains EC2/IMDS-related keywords, suggesting potential SSRF/metadata exposure risk. Response contains AWS credential or metadata references.",
                        recommendation="(1) Disable IMDSv1, require IMDSv2 with token-based auth. (2) Implement request filtering in application. (3) Use IAM roles instead of embedded credentials. (4) Run security assessment for SSRF vulnerabilities. (5) Manual verification required.",
                        frameworks=get_frameworks("AWS_IMDS_EXPOSURE_PATTERN"),
                        framework_mappings=[FrameworkMapping(**m) for m in get_framework_mappings("AWS_IMDS_EXPOSURE_PATTERN")],
                    )
                )
    except Exception:
        pass
    
    return findings


async def check_aws_waf(http_meta: dict) -> list[Finding]:
    """Check for AWS WAF absence signal (heuristic + manual review required)."""
    findings: list[Finding] = []
    
    # Heuristic: If we detect AWS services (CloudFront/ELB) but NO WAF indicators.
    # Note: Absence of header does NOT guarantee absence of WAF, so manual_review=true
    
    server = http_meta.get("server", "").lower()
    headers_lower = {k.lower(): v for k, v in http_meta.get("headers", {}).items()}
    
    # WAF presence indicators
    has_waf_indicators = (
        "waf" in server or
        any("waf" in str(v).lower() for v in headers_lower.values())
    )
    
    # AWS distribution presence indicators
    has_aws_distribution = (
        "cloudfront" in server or 
        "elb" in server or
        "elasticloadbalancing" in server or
        (headers_lower.get("via", "") and "cloudfront" in headers_lower.get("via", "").lower())
    )
    
    # Only raise finding if AWS distribution detected WITHOUT WAF indicators
    if has_aws_distribution and not has_waf_indicators:
        findings.append(
            Finding(
                code="AWS_WAF_ABSENT_SIGNAL",
                title="AWS WAF Not Detected on AWS Distribution",
                severity="medium",
                confidence="medium",
                check_status="passed",
                manual_review=True,
                confidence_reason="WAF absence based on header inspection; absence does not guarantee no WAF (WAF can be silent), requires manual AWS console verification",
                evidence=f"CloudFront/ELB distribution detected (Server: {http_meta.get('server', 'N/A')}, Via: {headers_lower.get('via', 'N/A')}) but no WAF indicators found in response headers. This is a heuristic assessment; explicit WAF detection requires additional investigation.",
                recommendation="Evaluate and consider enabling AWS WAF on CloudFront distributions and Application/Network Load Balancers to protect against common web application attacks (SQL injection, XSS, DDoS). Review AWS WAF rules and threat patterns relevant to your workload.",
                frameworks=get_frameworks("AWS_WAF_ABSENT_SIGNAL"),
                framework_mappings=[FrameworkMapping(**m) for m in get_framework_mappings("AWS_WAF_ABSENT_SIGNAL")],
            )
        )
    
    return findings


async def check_aws_route53(domain: str, dns_meta: dict = None) -> list[Finding]:
    """Check for Route53 misconfiguration signals using real NS lookup + pattern detection."""
    findings: list[Finding] = []
    
    if dns_meta is None:
        dns_meta = {}
    
    try:
        # Perform real NS lookup if possible
        ns_lookup = await resolve_nameservers(domain)
        dns_meta["route53_ns_lookup"] = ns_lookup
        
        if ns_lookup["status"] == "passed":
            # Successfully resolved NS records
            nameservers = ns_lookup["nameservers"]
            awsdns_nameservers = [ns for ns in nameservers if "awsdns" in ns.lower()]
            
            if awsdns_nameservers:
                # HIGH confidence: we have real NS records showing Route53
                findings.append(
                    Finding(
                        code="AWS_ROUTE53_MISCONFIG_SIGNAL",
                        title="AWS Route53 Nameservers Confirmed",
                        severity="medium",
                        confidence="high",
                        check_status="passed",
                        confidence_reason="Real NS lookup confirms .awsdns-* nameserver assignment (authoritative DNS record)",
                        evidence=f"Domain ({domain}) NS records resolved to AWS Route53 nameservers: {', '.join(awsdns_nameservers)}. Route53 is confirmed in use.",
                        recommendation="Review Route53 DNS records for proper configuration. Validate: (1) NS records point to correct AWS nameservers, (2) DNSSEC is enabled if required, (3) DNS failover and routing policies are intentional, (4) Access control is restricted.",
                        frameworks=get_frameworks("AWS_ROUTE53_MISCONFIG_SIGNAL"),
                        framework_mappings=[FrameworkMapping(**m) for m in get_framework_mappings("AWS_ROUTE53_MISCONFIG_SIGNAL")],
                    )
                )
        elif ns_lookup["status"] == "inconclusive":
            # DNS lookup inconclusive (dnspython not available or partial info)
            # Fall back to pattern detection
            domain_lower = domain.lower()
            if ".awsdns-" in domain_lower or "awsdns" in domain_lower:
                findings.append(
                    Finding(
                        code="AWS_ROUTE53_MISCONFIG_SIGNAL",
                        title="AWS Route53 DNS Configuration Suspected",
                        severity="medium",
                        confidence="medium",
                        check_status="inconclusive",
                        manual_review=True,
                        confidence_reason="Domain pattern suggests Route53 but authoritative DNS verification inconclusive (dnspython unavailable or DNS timeout)",
                        evidence=f"Domain ({domain}) contains .awsdns-* pattern. Route53 usage suspected but requires manual DNS verification.",
                        recommendation="Review Route53 DNS records for proper configuration. Use 'nslookup -type=NS {domain}' to verify nameserver assignment.",
                        frameworks=get_frameworks("AWS_ROUTE53_MISCONFIG_SIGNAL"),
                        framework_mappings=[FrameworkMapping(**m) for m in get_framework_mappings("AWS_ROUTE53_MISCONFIG_SIGNAL")],
                    )
                )
            
            # Check IP range heuristic as additional signal
            resolved_ips = dns_meta.get("resolved_ips", [])
            if resolved_ips and any(ip.startswith("205.251.193") or ip.startswith("205.251.194") for ip in resolved_ips):
                findings.append(
                    Finding(
                        code="AWS_ROUTE53_MISCONFIG_SIGNAL",
                        title="AWS Route53 Nameserver IP Range Detected",
                        severity="medium",
                        confidence="high",
                        check_status="passed",
                        confidence_reason="A/AAAA records resolve to AWS Route53 IP range (205.251.193/194.x) - strong heuristic",
                        evidence=f"Domain ({domain}) resolves to IP range 205.251.193.x or 205.251.194.x (AWS Route53 infrastructure).",
                        recommendation="Review Route53 configuration through AWS console.",
                        frameworks=get_frameworks("AWS_ROUTE53_MISCONFIG_SIGNAL"),
                        framework_mappings=[FrameworkMapping(**m) for m in get_framework_mappings("AWS_ROUTE53_MISCONFIG_SIGNAL")],
                    )
                )
        else:
            # NS lookup failed
            dns_meta["route53_lookup_error"] = ns_lookup.get("error", "Unknown error")
    except Exception as e:
        dns_meta["route53_check_exception"] = str(e)
    
    return findings


async def check_aws(domain: str, http_meta: dict = None, dns_meta: dict = None) -> tuple[list[Finding], dict]:
    """Orchestrate all AWS security checks."""
    findings: list[Finding] = []
    meta: dict = {
        "aws_services_detected": _detect_aws_service_patterns(domain),
        "checks_performed": []
    }
    
    if not http_meta:
        http_meta = {}
    if not dns_meta:
        dns_meta = {}
    
    try:
        # S3 check
        s3_findings, s3_meta = await check_aws_s3(domain)
        findings.extend(s3_findings)
        meta["s3"] = s3_meta
        meta["checks_performed"].append("S3")
        
        # CloudFront check
        cf_findings = await check_aws_cloudfront(domain, http_meta)
        findings.extend(cf_findings)
        meta["checks_performed"].append("CloudFront")
        
        # API Gateway check
        apigw_findings, apigw_meta = await check_aws_api_gateway(domain)
        findings.extend(apigw_findings)
        meta["apigw"] = apigw_meta
        meta["checks_performed"].append("API_Gateway")
        
        # ELB check
        elb_findings = await check_aws_elb(http_meta)
        findings.extend(elb_findings)
        meta["checks_performed"].append("ELB")
        
        # IMDS exposure check
        imds_findings = await check_aws_imds(domain)
        findings.extend(imds_findings)
        meta["checks_performed"].append("IMDS")
        
        # WAF check
        waf_findings = await check_aws_waf(http_meta)
        findings.extend(waf_findings)
        meta["checks_performed"].append("WAF")
        
        # Route53 check
        route53_findings = await check_aws_route53(domain, dns_meta)
        findings.extend(route53_findings)
        meta["checks_performed"].append("Route53")
        
    except Exception as e:
        meta["aws_check_error"] = str(e)
    
    return findings, meta
