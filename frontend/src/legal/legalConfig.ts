export const VALID_LEGAL_DOC_IDS = [
  'privacy',
  'terms',
  'acceptable-use',
  'ai-policy',
  'cookies',
  'dmca',
  'refunds',
  'about',
  'contact',
] as const;

export type LegalDocId = (typeof VALID_LEGAL_DOC_IDS)[number];

export function isLegalDocId(val: string): val is LegalDocId {
  return (VALID_LEGAL_DOC_IDS as readonly string[]).includes(val);
}

export interface LegalConfig {
  companyName: string;
  serviceName: string;
  websiteUrl: string;
  supportEmail: string;
  privacyEmail: string;
  dmcaEmail: string;
  abuseEmail: string;
  apiEmail: string;
  legalAddress: string;
  governingLaw: string;
  effectiveDate: string;
  lastUpdated: string;
  githubUrl: string;
}

export const LEGAL_CONFIG: LegalConfig = {
  companyName: 'Alpha Creations',
  serviceName: 'Kokoro Voice Studio',
  websiteUrl: typeof window !== 'undefined' ? window.location.origin : 'https://saytts.site',
  supportEmail: 'madushankamax8@gmail.com',
  privacyEmail: 'madushankamax8@gmail.com',
  dmcaEmail: 'madushankamax8@gmail.com',
  abuseEmail: 'madushankamax8@gmail.com',
  apiEmail: 'madushankamax8@gmail.com',
  legalAddress: 'Online Service / Remote Operator',
  governingLaw: 'Applicable Local Laws',
  effectiveDate: 'September 9, 2026',
  lastUpdated: 'September 9, 2026',
  githubUrl: 'https://github.com/dilshan916/kokoro-voice-studio',
};
