/**
 * Roadmap Generator
 * Converts gaps and findings into prioritized remediation tasks with 30/60/90-day roadmaps
 */

import { GapItem } from '@/lib/controls';

export interface RemediationTask {
  id: string;
  title: string;
  description: string;
  controlId?: string;
  findingId?: string;
  phase: '0-30' | '30-60' | '60-90';
  priority: 'critical' | 'high' | 'medium' | 'low';
  estimatedDays: number;
  effort: number; // 1-10
  owner?: string; // e.g., "CISO", "IT Manager", "Security Engineer"
  prerequisites: string[]; // Task IDs that must be completed first
  successCriteria: string[];
  resources?: string[]; // Tools, services, or training needed
}

export interface RemediationRoadmap {
  organizationId: string;
  phase0_30: RemediationTask[];
  phase30_60: RemediationTask[];
  phase60_90: RemediationTask[];
  totalEstimatedDays: number;
  generatedAt: Date;
}

/**
 * Remediation Task Templates
 * Maps control types to standard remediation tasks
 */
const REMEDIATION_TEMPLATES: Record<string, { title: string; baseEffort: number; successCriteria: string[] }> = {
  // Governance
  gov_policy: {
    title: 'Develop Information Security Policy',
    baseEffort: 5,
    successCriteria: [
      'Policy document drafted and reviewed',
      'Stakeholder sign-off obtained',
      'Policy communicated to all staff',
      'Training completed for key roles',
    ],
  },
  gov_bank_board_reporting: {
    title: 'Establish Board-Level Security Reporting',
    baseEffort: 6,
    successCriteria: [
      'Reporting metrics defined',
      'Dashboard/report template created',
      'First board presentation delivered',
      'Quarterly cadence established',
    ],
  },

  // IAM
  iam_mfa: {
    title: 'Implement Multi-Factor Authentication',
    baseEffort: 7,
    successCriteria: [
      'MFA solution selected and procured',
      'MFA rolled out to 100% of users',
      'Backup codes distributed',
      'Support process documented',
    ],
  },
  iam_bank_pam: {
    title: 'Deploy Privileged Access Management System',
    baseEffort: 9,
    successCriteria: [
      'PAM platform selected',
      'Proxy/gateway deployed',
      'Session recording enabled',
      'Privileged account inventory created',
    ],
  },
  iam_access_reviews: {
    title: 'Implement Access Review Process',
    baseEffort: 4,
    successCriteria: [
      'Access review procedure documented',
      'Quarterly review schedule established',
      'First review cycle completed',
      'Remediation process defined',
    ],
  },

  // Network Security
  net_firewall: {
    title: 'Deploy/Harden Network Firewalls',
    baseEffort: 6,
    successCriteria: [
      'Firewall rules inventory created',
      'Default-deny policy implemented',
      'Egress filtering enabled',
      'Log ingestion validated',
    ],
  },
  net_segmentation: {
    title: 'Implement Network Segmentation',
    baseEffort: 8,
    successCriteria: [
      'Network zones defined',
      'VLANs created',
      'ACLs configured',
      'Micro-segmentation tested',
    ],
  },

  // Data Protection
  data_encryption: {
    title: 'Enable Data Encryption (At Rest & In Transit)',
    baseEffort: 7,
    successCriteria: [
      'Sensitive data inventory created',
      'Encryption keys provisioned',
      'TLS 1.2+ enforced on all services',
      'Database encryption enabled',
    ],
  },

  // Incident Response
  ir_incident_response: {
    title: 'Develop Incident Response Plan',
    baseEffort: 6,
    successCriteria: [
      'Incident definition and scope defined',
      'Incident severity levels established',
      'Roles and responsibilities assigned',
      'Communication templates created',
      'First tabletop exercise conducted',
    ],
  },
  ir_bank_incident_response_plan: {
    title: 'Establish Formal Incident Response Procedure',
    baseEffort: 7,
    successCriteria: [
      'Procedure document with Board review',
      'Audit trail mechanisms implemented',
      'Escalation to regulatory bodies defined',
      'Legal review completed',
    ],
  },
  ir_bank_tabletop_exercises: {
    title: 'Conduct Annual Incident Response Tabletop',
    baseEffort: 4,
    successCriteria: [
      'Exercise scenario developed',
      'Board participation confirmed',
      'Exercise executed',
      'Lessons learned documented',
    ],
  },

  // Backup & Recovery
  dr_backups: {
    title: 'Implement Backup and Disaster Recovery',
    baseEffort: 7,
    successCriteria: [
      'Backup infrastructure deployed',
      'Daily backup schedule active',
      'Restoration tested quarterly',
      'RTO/RPO targets defined and met',
    ],
  },
  dr_bank_backup_testing: {
    title: 'Establish Quarterly Backup Testing Program',
    baseEffort: 5,
    successCriteria: [
      'Testing procedure documented',
      'Quarterly test schedule established',
      'Test results logged',
      'Issues remediated',
    ],
  },
};

/**
 * Generate remediation roadmap from gaps
 * Distributes tasks across 30/60/90-day phases based on criticality and effort
 */
export function generateRemediationRoadmap(
  organizationId: string,
  gaps: GapItem[]
): RemediationRoadmap {
  const tasks: RemediationTask[] = [];
  let taskId = 1;

  // Convert gaps to tasks
  gaps.forEach((gap) => {
    const template = REMEDIATION_TEMPLATES[gap.controlId] || {
      title: `Remediate: ${gap.controlName}`,
      baseEffort: gap.effort,
      successCriteria: ['Gap assessed', 'Remediation plan approved', 'Implementation completed'],
    };

    const task: RemediationTask = {
      id: `task_${taskId++}`,
      title: template.title,
      description: `Close gap in ${gap.domain}: ${gap.controlName} (Current: ${gap.currentLevel}%, Target: ${gap.targetLevel}%)`,
      controlId: gap.controlId,
      phase: '0-30', // Will be reassigned based on priority
      priority: gap.severity as any,
      estimatedDays: Math.ceil((template.baseEffort / 10) * 30), // Estimate based on effort
      effort: template.baseEffort,
      owner: assignOwner(gap.domain),
      prerequisites: [],
      successCriteria: template.successCriteria,
      resources: suggestResources(gap.domain),
    };

    tasks.push(task);
  });

  // Assign tasks to phases based on priority and effort
  const phase030: RemediationTask[] = [];
  const phase3060: RemediationTask[] = [];
  const phase6090: RemediationTask[] = [];

  // Sort by criticality first
  const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
  tasks.sort((a, b) => {
    const aPri = priorityOrder[a.priority];
    const bPri = priorityOrder[b.priority];
    if (aPri !== bPri) return aPri - bPri;
    return a.effort - b.effort;
  });

  // Distribute across phases
  let cumulativeDays30 = 0;
  let cumulativeDays60 = 0;

  tasks.forEach((task) => {
    if (task.priority === 'critical' || (cumulativeDays30 < 30 && task.effort <= 6)) {
      task.phase = '0-30';
      cumulativeDays30 += task.estimatedDays;
      phase030.push(task);
    } else if (task.priority === 'high' || (cumulativeDays60 < 30 && task.effort <= 7)) {
      task.phase = '30-60';
      cumulativeDays60 += task.estimatedDays;
      phase3060.push(task);
    } else {
      task.phase = '60-90';
      phase6090.push(task);
    }
  });

  const totalEstimatedDays = phase030.reduce((sum, t) => sum + t.estimatedDays, 0) +
    phase3060.reduce((sum, t) => sum + t.estimatedDays, 0) +
    phase6090.reduce((sum, t) => sum + t.estimatedDays, 0);

  return {
    organizationId,
    phase0_30: phase030,
    phase30_60: phase3060,
    phase60_90: phase6090,
    totalEstimatedDays,
    generatedAt: new Date(),
  };
}

/**
 * Assign owner role based on domain
 */
function assignOwner(domain: string): string {
  const ownerMap: Record<string, string> = {
    'Governance': 'CISO',
    'Identity & Access Management': 'Identity Manager',
    'Network Security': 'Network Engineer',
    'Data Protection': 'Data Security Officer',
    'Incident Response': 'Incident Response Lead',
    'Backup & Recovery': 'Infrastructure Manager',
    'Third-Party Risk': 'Vendor Manager',
  };
  return ownerMap[domain] || 'Security Manager';
}

/**
 * Suggest resources/tools for domain-specific remediation
 */
function suggestResources(domain: string): string[] {
  const resourceMap: Record<string, string[]> = {
    'Governance': ['Policy templates', 'Governance software', 'Training platform'],
    'Identity & Access Management': ['MFA solution', 'Directory service', 'PAM platform'],
    'Network Security': ['Firewall appliance', 'Security automation', 'Monitoring tools'],
    'Data Protection': ['Encryption tool', 'Key management service', 'DLP solution'],
    'Incident Response': ['SOAR platform', 'Communication tools', 'Forensics kit'],
    'Backup & Recovery': ['Backup software', 'Cloud storage', 'DRP testing platform'],
  };
  return resourceMap[domain] || [];
}

/**
 * Format roadmap for executive presentation
 */
export function formatRoadmapSummary(roadmap: RemediationRoadmap): string {
  const lines: string[] = [];

  lines.push('# 90-Day Remediation Roadmap\n');

  lines.push(`## Phase 1: Days 0-30 (${roadmap.phase0_30.length} tasks)`);
  lines.push('**Critical and high-priority gaps to close immediately.**\n');
  roadmap.phase0_30.forEach((task) => {
    lines.push(`- **${task.title}** (Owner: ${task.owner}, Effort: ${task.effort}/10)`);
    lines.push(`  Days: ${task.estimatedDays}, Priority: ${task.priority}\n`);
  });

  lines.push(`## Phase 2: Days 30-60 (${roadmap.phase30_60.length} tasks)`);
  lines.push('**Medium-term improvements to foundation.**\n');
  roadmap.phase30_60.forEach((task) => {
    lines.push(`- **${task.title}** (Owner: ${task.owner}, Effort: ${task.effort}/10)\n`);
  });

  lines.push(`## Phase 3: Days 60-90 (${roadmap.phase60_90.length} tasks)`);
  lines.push('**Long-term hardening and optimization.**\n');
  roadmap.phase60_90.forEach((task) => {
    lines.push(`- **${task.title}** (Owner: ${task.owner}, Effort: ${task.effort}/10)\n`);
  });

  lines.push(`\n**Total Estimated Timeline:** ${roadmap.totalEstimatedDays} days`);
  lines.push(`**Resource Allocation:** Distribute effort across phases based on team capacity.\n`);

  return lines.join('\n');
}
