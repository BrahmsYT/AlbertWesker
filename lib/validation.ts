import { z } from 'zod';

/**
 * Input Validation Schemas
 * All user inputs must be validated through these schemas before processing.
 */

// Domain validation for external scans
export const DomainSchema = z
  .string()
  .min(1, 'Domain is required')
  .max(255, 'Domain too long')
  .refine(
    (val) => {
      // Basic domain validation (no protocol, must look like domain)
      const domainPattern = /^([a-z0-9]([a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}$/i;
      return domainPattern.test(val);
    },
    'Invalid domain format'
  );

// Assessment name validation
export const AssessmentNameSchema = z
  .string()
  .min(3, 'Assessment name must be at least 3 characters')
  .max(200, 'Assessment name too long')
  .refine(
    (val) => !/[<>{}"`]/.test(val),
    'Assessment name contains invalid characters'
  );

// Organization name validation
export const OrgNameSchema = z
  .string()
  .min(2, 'Organization name must be at least 2 characters')
  .max(256, 'Organization name too long')
  .refine(
    (val) => !/[<>{}"`]/.test(val),
    'Organization name contains invalid characters'
  );

// Action/Risk title validation
export const TitleSchema = z
  .string()
  .min(3, 'Title must be at least 3 characters')
  .max(500, 'Title too long')
  .refine(
    (val) => !/[<>{}"`]/.test(val),
    'Title contains invalid characters'
  );

// Description/Notes validation - block HTML/script tags and dangerous patterns
export const DescriptionSchema = z
  .string()
  .min(1, 'Description is required')
  .max(5000, 'Description too long')
  .refine(
    (val) => !/(<script|<iframe|<object|<embed|javascript:|onerror=|onclick=)/i.test(val),
    'Description contains potentially unsafe content (scripts, event handlers, etc.)'
  );

// Scan result validation
export const ScanResultSchema = z.object({
  domain: DomainSchema,
  findings: z.array(
    z.object({
      title: TitleSchema,
      description: DescriptionSchema,
      severity: z.enum(['Critical', 'High', 'Medium', 'Low']),
      domain: z.string().max(100),
      frameworkMapping: z.array(z.string()).min(1),
    })
  ),
  scannedAt: z.string().datetime(),
  source: z.enum(['external_scan', 'internal_collector', 'manual']).optional(),
});

export type ScanResult = z.infer<typeof ScanResultSchema>;

/**
 * Sanitization helper: removes potentially dangerous characters
 */
export function sanitizeInput(input: string): string {
  return input
    .replace(/[<>]/g, '') // Remove angle brackets
    .trim();
}

/**
 * Safe JSON parsing with fallback
 */
export function safeJsonParse<T>(input: string, fallback: T): T {
  try {
    return JSON.parse(input) as T;
  } catch {
    return fallback;
  }
}
