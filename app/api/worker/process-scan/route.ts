import { NextResponse } from 'next/server';
import { processScanJob, processQueuedJobs } from '@/lib/scan-worker';

/**
 * POST /api/worker/process-scan
 * Process a specific scan job by ID
 * Requires WORKER_SECRET in Authorization header (for MVP security)
 * In production: use service account authentication
 */
export async function POST(req: Request) {
  try {
    const authHeader = req.headers.get('Authorization');
    const workerSecret = process.env.WORKER_SECRET || 'dev-secret';

    // Very basic auth - in production use proper service account
    if (authHeader !== `Bearer ${workerSecret}`) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await req.json();
    const { jobId } = body;

    if (!jobId) {
      return NextResponse.json({ error: 'jobId is required' }, { status: 400 });
    }

    const result = await processScanJob(jobId);

    if (!result.success) {
      return NextResponse.json({ error: result.error }, { status: 500 });
    }

    return NextResponse.json({
      success: true,
      jobId,
      message: 'Scan job processed successfully',
    });
  } catch (error) {
    console.error('[WORKER API] Error:', error);
    return NextResponse.json(
      { error: 'Failed to process scan job' },
      { status: 500 }
    );
  }
}

/**
 * POST /api/worker/process-queue
 * Process all queued scan jobs
 * For use with Cloud Scheduler or cron triggers
 * Requires WORKER_SECRET authentication
 */
export async function PUT(req: Request) {
  try {
    const authHeader = req.headers.get('Authorization');
    const workerSecret = process.env.WORKER_SECRET || 'dev-secret';

    if (authHeader !== `Bearer ${workerSecret}`) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const result = await processQueuedJobs();

    return NextResponse.json({
      success: true,
      processed: result.processed,
      failed: result.failed,
      message: `Processed ${result.processed} jobs, ${result.failed} failed`,
    });
  } catch (error) {
    console.error('[WORKER API] Queue processing error:', error);
    return NextResponse.json(
      { error: 'Failed to process job queue' },
      { status: 500 }
    );
  }
}
