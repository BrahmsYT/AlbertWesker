<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# CyberGap AI - Cybersecurity Risk & Compliance Platform

An AI-powered platform for external and internal cybersecurity gap analysis, compliance assessment, and remediation roadmap generation for banks and companies.

## Quick Start

**Prerequisites:**
- Node.js 18+
- Firebase project with Authentication and Firestore enabled
- Google Gemini API key

### Local Development

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.local.example .env.local
   ```
   Then edit `.env.local` with your values:
   - `NEXT_PUBLIC_FIREBASE_API_KEY`: Firebase project API key
   - `NEXT_PUBLIC_GEMINI_API_KEY`: Google Gemini API key (used in browser for AI features)

3. **Run development server:**
   ```bash
   npm run dev
   ```
   Open http://localhost:3000

## Architecture

- **Frontend:** Next.js 15 + React 19, Tailwind CSS
- **Backend:** Firebase (Auth + Firestore)
- **AI:** Google Gemini API
- **Security:** TLS encryption, tenant isolation, audit logging

## Features

- **External Scanning:** Assess public-facing domains for security gaps
- **Internal Analysis:** On-prem agent for LAN discovery and physical device analysis (camera, printer, scanner, workstation)
- **Framework Mappings:** ISO 27001, NIST CSF, CIS Controls, Bank Regulatory Baseline
- **Org-Specific Standards:** Custom control profiles and scoring
- **Roadmap Generation:** Deterministic 30/60/90-day remediation plans
- **AI Assistant:** Chat-based guidance on findings and remediation
- **Reports:** Executive summaries and technical annexes (coming soon)

## Testing & Validation

### Scanner Accuracy Benchmarking

The platform includes a comprehensive benchmark harness to validate scanner precision, recall, and false positive rates.

**Running the Benchmark:**

1. **Via Web UI:**
   - Navigate to `/admin/accuracy-test`
   - Click "Run Accuracy Test"
   - View results: precision, recall, F1 score, and fixture-level breakdown

2. **Programmatically (Node.js):**
   ```typescript
   import { validateAccuracyGate } from '@/lib/scanner-benchmark';
   
   const { passed, message, metrics } = await validateAccuracyGate();
   console.log(message);
   // Precision >= 0.90, False Positive Rate <= 0.10, All tests pass
   ```

**Benchmark Fixtures:**
- `secure-bank-example.com`: Baseline secure domain (expect minimal findings)
- `poorly-configured-example.com`: Multiple issues across DNS, TLS, HTTP headers
- `mixed-security-example.com`: Partial issues (some security gaps, some controls in place)

**Accuracy Gates (Production Requirements):**
- **Precision >= 0.90:** Of all findings reported, at least 90% must be true positives
- **False Positive Rate <= 0.10:** No more than 10% of findings can be false positives
- **All fixtures must pass:** F1 Score >= 0.80 for each test domain

### Immediate Scan Testing

For development and validation, scans can be triggered immediately (synchronously) instead of queued:

```bash
curl -X POST http://localhost:3000/api/scan \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "example.com",
    "organizationId": "org-uuid",
    "immediate": true
  }'
```

**Response:**
```json
{
  "jobId": "scan_1234567890_abc123",
  "status": "running",
  "domain": "example.com",
  "createdAt": "2025-01-15T10:30:00Z",
  "message": "Scan job created and processing started."
}
```

When `immediate: true`, the scanner runs synchronously and returns findings after processing completes.

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for cloud and on-prem setup instructions.

## Security Note

Never commit `.env.local` with real API keys to version control.
