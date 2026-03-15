export interface Question {
  id: string;
  domain: string;
  text: string;
  type: 'Bank' | 'Company' | 'Both';
  frameworks: string[];
}

export const QUESTIONS: Question[] = [
  {
    id: 'gov_1',
    domain: 'Governance',
    text: 'Is there a formally approved Information Security Policy?',
    type: 'Both',
    frameworks: ['ISO27001', 'NIST_CSF', 'CIS_CONTROLS', 'BANK_REG']
  },
  {
    id: 'gov_2',
    domain: 'Governance',
    text: 'Is there a designated CISO or equivalent security leader?',
    type: 'Both',
    frameworks: ['ISO27001', 'NIST_CSF', 'BANK_REG']
  },
  {
    id: 'gov_bank_1',
    domain: 'Governance',
    text: 'Are security reports presented to the Board of Directors at least annually?',
    type: 'Bank',
    frameworks: ['BANK_REG']
  },
  {
    id: 'iam_1',
    domain: 'Identity & Access Management',
    text: 'Is Multi-Factor Authentication (MFA) enforced for all external access?',
    type: 'Both',
    frameworks: ['ISO27001', 'NIST_CSF', 'CIS_CONTROLS', 'BANK_REG']
  },
  {
    id: 'iam_2',
    domain: 'Identity & Access Management',
    text: 'Are access rights reviewed at regular intervals?',
    type: 'Both',
    frameworks: ['ISO27001', 'NIST_CSF', 'CIS_CONTROLS']
  },
  {
    id: 'iam_bank_1',
    domain: 'Identity & Access Management',
    text: 'Is Privileged Access Management (PAM) implemented with session recording?',
    type: 'Bank',
    frameworks: ['BANK_REG']
  },
  {
    id: 'net_1',
    domain: 'Network Security',
    text: 'Are firewalls deployed to restrict unauthorized traffic?',
    type: 'Both',
    frameworks: ['ISO27001', 'NIST_CSF', 'CIS_CONTROLS', 'BANK_REG']
  },
  {
    id: 'data_1',
    domain: 'Data Protection',
    text: 'Is sensitive data encrypted at rest and in transit?',
    type: 'Both',
    frameworks: ['ISO27001', 'NIST_CSF', 'CIS_CONTROLS', 'BANK_REG']
  },
  {
    id: 'ir_1',
    domain: 'Incident Response',
    text: 'Is there a documented Incident Response Plan?',
    type: 'Both',
    frameworks: ['ISO27001', 'NIST_CSF', 'CIS_CONTROLS', 'BANK_REG']
  },
  {
    id: 'ir_bank_1',
    domain: 'Incident Response',
    text: 'Are incident response tabletop exercises conducted at least annually?',
    type: 'Bank',
    frameworks: ['BANK_REG']
  },
  {
    id: 'dr_1',
    domain: 'Backup & Recovery',
    text: 'Are critical systems backed up and tested for restoration?',
    type: 'Both',
    frameworks: ['ISO27001', 'NIST_CSF', 'CIS_CONTROLS', 'BANK_REG']
  },
  {
    id: 'tp_1',
    domain: 'Third-Party Risk',
    text: 'Are third-party vendors assessed for security risks before onboarding?',
    type: 'Both',
    frameworks: ['ISO27001', 'NIST_CSF', 'BANK_REG']
  }
];
