import { auth, db } from '@/lib/firebase';
import { doc, getDoc } from 'firebase/firestore';

/**
 * Tenant Isolation Guards
 * All APIs must verify that the current user belongs to the requested organization
 * before returning or modifying any data.
 */

interface TenantContext {
  userId: string;
  organizationId: string;
  role: string;
}

/**
 * Verify that current user has access to the organization
 * Throws error if unauthorized
 */
export async function verifyTenantAccess(
  userId: string,
  organizationId: string
): Promise<TenantContext> {
  if (!userId || !organizationId) {
    throw new Error('User and organization IDs are required');
  }

  try {
    // Check if user is admin
    const userRef = doc(db, 'users', userId);
    const userSnap = await getDoc(userRef);
    if (userSnap.exists() && userSnap.data().role === 'admin') {
      return {
        userId,
        organizationId,
        role: 'admin',
      };
    }

    // Check if user has membership in this organization
    const membershipRef = doc(db, 'memberships', `${userId}_${organizationId}`);
    const membershipSnap = await getDoc(membershipRef);

    if (!membershipSnap.exists()) {
      throw new Error('Unauthorized: No membership found');
    }

    const membership = membershipSnap.data();
    return {
      userId,
      organizationId,
      role: membership.role,
    };
  } catch (error) {
    console.error('Tenant verification failed:', error);
    throw new Error('Unauthorized: Tenant access denied');
  }
}

/**
 * Rate limiting helper
 * In production, use Redis. For MVP, use in-memory Map with stable time windows.
 * Windows are based on minute start time to prevent reset by adding new date component.
 */
const rateLimitMap = new Map<string, { count: number; windowStart: number }>();

export function checkRateLimit(
  key: string,
  limit: number = 10,
  windowMs: number = 60000
): { allowed: boolean; remaining: number } {
  const now = Date.now();
  const currentWindow = Math.floor(now / windowMs) * windowMs;
  const entry = rateLimitMap.get(key);

  // If no entry or window has changed, start a new window
  if (!entry || entry.windowStart !== currentWindow) {
    rateLimitMap.set(key, { count: 1, windowStart: currentWindow });
    return { allowed: true, remaining: limit - 1 };
  }

  // Within same window, check if limit exceeded
  if (entry.count >= limit) {
    // Calculate seconds until window reset
    const resetTime = entry.windowStart + windowMs;
    const secondsRemaining = Math.ceil((resetTime - now) / 1000);
    console.warn(`[RATE_LIMIT] Key ${key} exceeded limit ${limit} in window. Reset in ${secondsRemaining}s`);
    return { allowed: false, remaining: 0 };
  }

  // Increment and return
  entry.count++;
  return { allowed: true, remaining: limit - entry.count };
}

/**
 * Audit logging placeholder
 * In production, log to Firestore collection: audit_logs
 */
export async function auditLog(
  userId: string,
  organizationId: string,
  action: string,
  resourceType: string,
  resourceId: string,
  outcome: 'success' | 'failure',
  details?: Record<string, any>
): Promise<void> {
  // For MVP, just log to console
  // TODO: Implement Firestore audit_logs collection
  console.log('[AUDIT]', {
    timestamp: new Date().toISOString(),
    userId,
    organizationId,
    action,
    resourceType,
    resourceId,
    outcome,
    details,
  });
}
