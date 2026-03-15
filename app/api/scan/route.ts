import { NextResponse } from 'next/server';
import { db } from '@/lib/firebase';
import { collection, setDoc, doc, Timestamp, getDoc } from 'firebase/firestore';
import { DomainSchema } from '@/lib/validation';
import { verifyTenantAccess, checkRateLimit, auditLog } from '@/lib/security';
import { processScanJob } from '@/lib/scan-worker';
import { validateBearerToken } from '@/lib/firebase-admin';
import { z } from 'zod';

/**
 * POST /api/scan
 * Create a new external scan job
 * 
 * Request body:
 * {
 *   organizationId: string (uuid)
 *   domain: string (e.g., "example.com")
 * }
 * 
 * Response:
 * {
 *   jobId: string
 *   status: "queued" | "running" | "completed" | "failed"
 *   domain: string
 *   createdAt: ISO datetime
 * }
 */
export async function POST(req: Request) {
  try {
    // 1. Parse and validate request
    const body = await req.json();
    const { organizationId, domain } = body;

    if (!organizationId || !domain) {
      return NextResponse.json(
        { error: 'organizationId and domain are required' },
        { status: 400 }
      );
    }

    // Validate domain format
    let validatedDomain: string;
    try {
      // Remove protocol if present
      validatedDomain = domain
        .replace(/^https?:\/\//, '')
        .split('/')[0]
        .toLowerCase();
      validatedDomain = DomainSchema.parse(validatedDomain);
    } catch (err) {
      if (err instanceof z.ZodError) {
        return NextResponse.json(
          { error: `Invalid domain: ${err.errors[0].message}` },
          { status: 400 }
        );
      }
      throw err;
    }

    // 2. Extract and verify user from Authorization header
    const authHeader = req.headers.get('Authorization');
    if (!authHeader?.startsWith('Bearer ')) {
      return NextResponse.json(
        { error: 'Missing or invalid Authorization header' },
        { status: 401 }
      );
    }

    let userId: string;
    try {
      // Verify token signature with Firebase Admin SDK
      const token = authHeader.slice(7); // Remove \"Bearer \" prefix\n      const decodedToken = await validateBearerToken(authHeader);\n      userId = decodedToken.uid;\n      \n      if (!userId) {\n        return NextResponse.json(\n          { error: 'Token missing user ID' },\n          { status: 401 }\n        );\n      }\n    } catch (err) {\n      return NextResponse.json(\n        { error: `Token verification failed: ${err instanceof Error ? err.message : 'Unknown error'}` },
        { status: 401 }
      );
    }

    // 3. Rate limiting check with stable key
    // Key format ensures one limit window per org per user
    const rateLimitKey = `scan:${organizationId}:${userId}`;
    const rateCheck = checkRateLimit(rateLimitKey, 5, 60000);
    if (!rateCheck.allowed) {
      return NextResponse.json(
        { error: 'Rate limit exceeded. Max 5 scans per minute.' },
        { status: 429 }
      );
    }

    // 4. Verify tenant access
    try {
      await verifyTenantAccess(userId, organizationId);
    } catch (authErr) {
      await auditLog(userId, organizationId, 'scan_create', 'domain', validatedDomain, 'failure', {
        reason: 'unauthorized',
      });
      return NextResponse.json({ error: 'Unauthorized' }, { status: 403 });
    }

    // 5. Create scan job in Firestore
    const jobId = `scan_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
    const jobRef = doc(collection(db, 'scan_jobs'), jobId);

    const jobData = {
      jobId,
      organizationId,
      domain: validatedDomain,
      status: 'queued', // queued -> running -> completed || failed
      createdAt: Timestamp.now(),
      createdBy: userId,
      updatedAt: Timestamp.now(),
      findings: [],
      error: null,
      retryCount: 0,
      maxRetries: 3,
      domainVerified: false, // TODO: Implement domain ownership verification
      verificationToken: null,
      expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000), // 7-day retention
    };

    await setDoc(jobRef, jobData);

    await auditLog(userId, organizationId, 'scan_create', 'domain', validatedDomain, 'success', {
      jobId,
    });

    // Optional: Trigger worker immediately if requested (for MVP development/testing)
    const immediate = body.immediate === true;
    if (immediate) {
      // Fire and forget: don't block response while processing
      processScanJob(jobId).catch((err) => {
        console.error(`Failed to process job ${jobId} immediately:`, err);
        auditLog(userId, organizationId, 'scan_process', 'jobId', jobId, 'failure', {
          reason: 'immediate_processing_failed',
          error: err instanceof Error ? err.message : 'Unknown',
        }).catch(() => {
          /* audit log error, but don't crash */
        });
      });
    }

    return NextResponse.json({
      jobId,
      status: immediate ? 'running' : 'queued',
      domain: validatedDomain,
      createdAt: new Date().toISOString(),
      message: immediate
        ? 'Scan job created and processing started.'
        : 'Scan job created. Polling will start automatically in the dashboard.',
    });
  } catch (error) {
    console.error('Scan API Error:', error);
    return NextResponse.json(
      { error: 'Failed to create scan job' },
      { status: 500 }
    );
  }
}

/**
 * GET /api/scan?jobId=xyz
 * Get scan job status and results
 */
export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const jobId = searchParams.get('jobId');

    if (!jobId) {
      return NextResponse.json({ error: 'jobId is required' }, { status: 400 });
    }

    // Fetch job from Firestore
    const jobRef = doc(db, 'scan_jobs', jobId);
    const jobSnap = await getDoc(jobRef);

    if (!jobSnap.exists()) {
      return NextResponse.json(
        { error: 'Scan job not found' },
        { status: 404 }
      );
    }

    const jobData = jobSnap.data();

    // Return current job status and findings
    return NextResponse.json({
      jobId: jobData.jobId,
      status: jobData.status,
      domain: jobData.domain,
      organizationId: jobData.organizationId,
      createdAt: jobData.createdAt?.toDate?.()?.toISOString?.() || jobData.createdAt,
      updatedAt: jobData.updatedAt?.toDate?.()?.toISOString?.() || jobData.updatedAt,
      findings: jobData.findings || [],
      error: jobData.error || null,
      progress: jobData.status === 'running' ? { current: jobData.progressCurrent || 0, total: jobData.progressTotal || 100 } : null,
      retryCount: jobData.retryCount || 0,
      maxRetries: jobData.maxRetries || 3,
    });
  } catch (error) {
    console.error('Scan Status API Error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch scan status' },
      { status: 500 }
    );
  }
}
