/**
 * Control Framework Definitions
 * Maps security controls to frameworks and defines scoring weights
 */

export interface Control {
  id: string;
  domain: string; // e.g., "Governance", "IAM", "Network Security"
  name: string;
  description: string;
  frameworks: Framework[];
  weight: number; // 1-100, importance factor
  criticality: 'low' | 'medium' | 'high' | 'critical';
  effort: number; // 1-10, implementation complexity
  targetLevel: number; // 0-100, compliance target
}

export type Framework = 'ISO27001' | 'NIST_CSF' | 'CIS_CONTROLS' | 'BANK_REG';

export interface ControlProfile {
  organizationId: string;
  name: string; // e.g., "Bank Regulatory Baseline", "Company Standard"
  type: 'Bank' | 'Company' | 'Custom';
  controls: Control[];
  createdAt: Date;
  updatedAt: Date;
}

/**
 * Bank Regulatory Baseline Controls
 * Stricter requirements for financial institutions
 */
export const BANK_REG_CONTROLS: Control[] = [
  {
    id: 'gov_bank_board_reporting',
    domain: 'Governance',
    name: 'Board-Level Security Reporting',
    description: 'Security reports presented to Board of Directors at least quarterly',
    frameworks: ['BANK_REG'],
    weight: 100,
    criticality: 'critical',
    effort: 5,
    targetLevel: 100,
  },
  {
    id: 'iam_bank_pam',
    domain: 'Identity & Access Management',
    name: 'Privileged Access Management (PAM)',
    description: 'PAM system with session recording and activity monitoring for critical accounts',
    frameworks: ['BANK_REG'],
    weight: 90,
    criticality: 'critical',
    effort: 8,
    targetLevel: 100,
  },
  {
    id: 'iam_bank_mfa',
    domain: 'Identity & Access Management',
    name: 'Multi-Factor Authentication (MFA)',
    description: 'MFA enforced for all banking channels and administrative access',
    frameworks: ['BANK_REG', 'ISO27001', 'NIST_CSF'],
    weight: 85,
    criticality: 'critical',
    effort: 6,
    targetLevel: 100,
  },
  {
    id: 'ir_bank_incident_response_plan',
    domain: 'Incident Response',
    name: 'Documented Incident Response Plan',
    description: 'Formal incident response procedure with defined roles, escalation, and audit trail',
    frameworks: ['BANK_REG', 'ISO27001', 'NIST_CSF'],
    weight: 80,
    criticality: 'critical',
    effort: 7,
    targetLevel: 100,
  },
  {
    id: 'ir_bank_tabletop_exercises',
    domain: 'Incident Response',
    name: 'Incident Response Tabletoop Exercises',
    description: 'Annual tabletop exercises with Board and senior management participation',
    frameworks: ['BANK_REG'],
    weight: 75,
    criticality: 'high',
    effort: 5,
    targetLevel: 100,
  },
  {
    id: 'dr_bank_backup_testing',
    domain: 'Backup & Recovery',
    name: 'Backup and Disaster Recovery Testing',
    description: 'Quarterly testing and validation of backup systems and recovery procedures',
    frameworks: ['BANK_REG', 'ISO27001', 'NIST_CSF'],
    weight: 85,
    criticality: 'critical',
    effort: 6,
    targetLevel: 100,
  },
];

/**
 * Company Standard (Generic) Controls
 * General security baseline for non-financial organizations
 */
export const COMPANY_STANDARD_CONTROLS: Control[] = [
  {
    id: 'gov_policy',
    domain: 'Governance',
    name: 'Information Security Policy',
    description: 'Documented and communicated information security policy',
    frameworks: ['ISO27001', 'NIST_CSF', 'CIS_CONTROLS'],
    weight: 70,
    criticality: 'high',
    effort: 4,
    targetLevel: 100,
  },
  {
    id: 'iam_mfa',
    domain: 'Identity & Access Management',
    name: 'Multi-Factor Authentication',
    description: 'MFA enabled for VPN, email, and administrative systems',
    frameworks: ['ISO27001', 'NIST_CSF', 'CIS_CONTROLS'],
    weight: 80,
    criticality: 'critical',
    effort: 5,
    targetLevel: 100,
  },
  {
    id: 'iam_access_reviews',
    domain: 'Identity & Access Management',
    name: 'Regular Access Reviews',
    description: 'Quarterly reviews of user access rights and privilege removal',
    frameworks: ['ISO27001', 'NIST_CSF'],
    weight: 65,
    criticality: 'high',
    effort: 4,
    targetLevel: 100,
  },
  {
    id: 'net_firewall',
    domain: 'Network Security',
    name: 'Firewall Protection',
    description: 'Network firewalls deployed and configured with restrictive default policies',
    frameworks: ['ISO27001', 'NIST_CSF', 'CIS_CONTROLS'],
    weight: 75,
    criticality: 'critical',
    effort: 3,
    targetLevel: 100,
  },
  {
    id: 'net_segmentation',
    domain: 'Network Security',
    name: 'Network Segmentation',
    description: 'Network segmented into security zones with controlled inter-zone traffic',
    frameworks: ['ISO27001', 'NIST_CSF'],
    weight: 70,
    criticality: 'high',
    effort: 7,
    targetLevel: 100,
  },
  {
    id: 'data_encryption',
    domain: 'Data Protection',
    name: 'Data Encryption',
    description: 'Sensitive data encrypted at rest (AES-256) and in transit (TLS 1.2+)',
    frameworks: ['ISO27001', 'NIST_CSF', 'CIS_CONTROLS'],
    weight: 85,
    criticality: 'critical',
    effort: 6,
    targetLevel: 100,
  },
  {
    id: 'ir_incident_response',
    domain: 'Incident Response',
    name: 'Incident Response Plan',
    description: 'Documented incident response procedure with defined escalation',
    frameworks: ['ISO27001', 'NIST_CSF'],
    weight: 75,
    criticality: 'high',
    effort: 5,
    targetLevel: 100,
  },
  {
    id: 'dr_backups',
    domain: 'Backup & Recovery',
    name: 'Regular Backups',
    description: 'Critical systems backed up daily with tested restoration procedures',
    frameworks: ['ISO27001', 'NIST_CSF', 'CIS_CONTROLS'],
    weight: 80,
    criticality: 'critical',
    effort: 4,
    targetLevel: 100,
  },
];

/**
 * Get default control profile based on organization type
 */
export function getDefaultControlProfile(
  organizationId: string,
  orgType: 'Bank' | 'Company'
): ControlProfile {
  const controls = orgType === 'Bank' ? BANK_REG_CONTROLS : COMPANY_STANDARD_CONTROLS;

  return {
    organizationId,
    name: orgType === 'Bank' ? 'Bank Regulatory Baseline' : 'Company Security Standard',
    type: orgType,
    controls,
    createdAt: new Date(),
    updatedAt: new Date(),
  };
}

/**
 * Scoring Model
 * Calculates compliance and risk scores based on control assessment
 */
export interface ComplianceScore {
  totalScore: number; // 0-100, average across all controls
  completionPercentage: number; // % of controls assessed
  domainScores: Record<string, number>; // Score per domain
  gapAnalysis: GapItem[];
  riskScore: number; // 0-100, inverse of compliance (higher = more risk)
}

export interface GapItem {
  controlId: string;
  controlName: string;
  domain: string;
  currentLevel: number; // 0-100, what's implemented
  targetLevel: number; // 0-100, what's required
  gap: number; // targetLevel - currentLevel
  severity: 'low' | 'medium' | 'high' | 'critical';
  effort: number; // 1-10, effort to close gap
}

/**
 * Calculate compliance score from control assessments
 */
export function calculateComplianceScore(
  controls: Control[],
  assessments: Record<string, number> // { controlId: currentLevel }
): ComplianceScore {
  let totalWeightedScore = 0;
  let totalWeight = 0;
  let assessedCount = 0;
  const domainScores: Record<string, { score: number; weight: number }> = {};
  const gaps: GapItem[] = [];

  controls.forEach((control) => {
    const currentLevel = assessments[control.id] ?? 0;
    assessedCount += 1;

    // Weight the control score
    const weightedScore = currentLevel * control.weight;
    totalWeightedScore += weightedScore;
    totalWeight += control.weight;

    // Domain scoring
    if (!domainScores[control.domain]) {
      domainScores[control.domain] = { score: 0, weight: 0 };
    }
    domainScores[control.domain].score += weightedScore;
    domainScores[control.domain].weight += control.weight;

    // Gap analysis
    const gap = control.targetLevel - currentLevel;
    if (gap > 0) {
      let severity: 'low' | 'medium' | 'high' | 'critical' = 'low';
      if (control.criticality === 'critical' && gap > 50) severity = 'critical';
      else if (control.criticality === 'high' && gap > 30) severity = 'high';
      else if (gap > 50) severity = 'high';
      else if (gap > 20) severity = 'medium';

      gaps.push({
        controlId: control.id,
        controlName: control.name,
        domain: control.domain,
        currentLevel,
        targetLevel: control.targetLevel,
        gap,
        severity,
        effort: control.effort,
      });
    }
  });

  // totalWeightedScore is already in 0-100 scale (weighted sum / total weight * 100)
  // Apply rounding cleanly to 0-100 range
  const totalScore = totalWeight > 0 ? Math.round((totalWeightedScore / totalWeight)) : 0;
  
  // completionPercentage: count only controls that have a non-zero assessment
  const assessedWithValueCount = Object.values(assessments).filter(val => val > 0).length;
  const completionPercentage = controls.length > 0 ? Math.round((assessedWithValueCount / controls.length) * 100) : 0;

  // Calculate domain-level scores - normalize to 0-100
  const domainScoreMap: Record<string, number> = {};
  Object.entries(domainScores).forEach(([domain, { score, weight }]) => {
    // score is already weighted, divide by weight to get average, then ensure 0-100
    domainScoreMap[domain] = weight > 0 ? Math.min(100, Math.round((score / weight))) : 0;
  });

  // Sort gaps by severity and effort
  gaps.sort((a, b) => {
    const severityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
    const aSev = severityOrder[a.severity];
    const bSev = severityOrder[b.severity];
    if (aSev !== bSev) return bSev - aSev;
    return a.effort - b.effort; // Lower effort first
  });

  return {
    totalScore,
    completionPercentage,
    domainScores: domainScoreMap,
    gapAnalysis: gaps,
    riskScore: Math.max(0, 100 - totalScore),
  };
}
