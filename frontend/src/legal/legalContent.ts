/**
 * Kokoro Voice Studio — Production Legal Content & Policy Registry
 * =================================================================
 * Structured, verified legal and company documentation adhering strictly to the
 * technical audit of the Kokoro Voice Studio application.
 *
 * GROUND-TRUTH PRINCIPLES:
 * 1. Zero-login architecture: User identity is based on anonymous client device IDs (X-Device-Id).
 * 2. On-premise Kokoro-82M ONNX inference: User text is processed on-premise and NOT sent to external third-party AI APIs.
 * 3. Local browser history: Recent generations are kept client-side in HTML5 localStorage (kokoro_history).
 * 4. Temporary server files: Rendered audio and subtitles reside temporarily on the host server filesystem (output/).
 * 5. Cookies: Zero first-party tracking cookies. Cloudflare security cookies and Google Fonts used.
 * 6. Advertising: Google AdSense is currently an unactivated placeholder; no third-party ads are currently delivered.
 * 7. Payments: Automated recurring subscriptions are securely processed via a certified PCI-DSS Level 1 payment processor ($9.99/mo Pro Unlimited). Card data is handled directly by the processor's compliant infrastructure and never stored on our servers. Promotional VIP license keys are also supported.
 * 8. Generated Audio Rights: Clear distinction between input rights, synthetic output licenses, and copyright eligibility limitations.
 * 9. Placeholders: Clearly marked configuration tokens for unverified legal entity and contact details.
 */

import {
  type LegalDocId,
  VALID_LEGAL_DOC_IDS,
  isLegalDocId,
  type LegalConfig,
  LEGAL_CONFIG,
} from './legalConfig';

export {
  type LegalDocId,
  VALID_LEGAL_DOC_IDS,
  isLegalDocId,
  type LegalConfig,
  LEGAL_CONFIG,
};

export interface LegalSection {
  id: string;
  title: string;
  content: string[];
}

export interface LegalDocument {
  id: LegalDocId;
  title: string;
  shortTitle: string;
  subtitle: string;
  iconName: 'Shield' | 'FileText' | 'AlertTriangle' | 'Sparkles' | 'Cookie' | 'Scale' | 'RefreshCw' | 'Info' | 'Mail';
  effectiveDate: string;
  lastUpdated: string;
  sections: LegalSection[];
}

export const ALL_LEGAL_DOCS: LegalDocument[] = [
  // ==========================================================================
  // 1. PRIVACY POLICY
  // ==========================================================================
  {
    id: 'privacy',
    title: 'Privacy Policy',
    shortTitle: 'Privacy',
    subtitle: 'Transparent disclosures regarding data handling, zero-login architecture, on-premise AI inference, and user rights.',
    iconName: 'Shield',
    effectiveDate: LEGAL_CONFIG.effectiveDate,
    lastUpdated: LEGAL_CONFIG.lastUpdated,
    sections: [
      {
        id: 'overview',
        title: '1. Overview & Architectural Principles',
        content: [
          `This Privacy Policy explains how ${LEGAL_CONFIG.serviceName} ("we," "us," or "our") processes information in connection with our web application, desktop application, and developer APIs.`,
          `Our service is built around a zero-login architecture. You are not required to create a personal account, register an email address, or supply a password to synthesize speech. Identity and monthly character allowances are managed through anonymous, client-generated device identifiers rather than personal profiles.`,
          `We believe in data minimization: we collect only what is strictly necessary to route network requests, enforce monthly character quotas, prevent denial-of-service abuse, and deliver your requested audio files.`,
        ],
      },
      {
        id: 'information-collected',
        title: '2. Information We Collect & How It Is Collected',
        content: [
          `A. Anonymous Device Identifier (X-Device-Id): When you access the application, your browser generates a random hexadecimal identifier (prefixed with "dev_web_") stored in your browser's HTML5 localStorage. This identifier is transmitted in request headers solely to track your monthly character quota and associate optional API keys.`,
          `B. Text Submitted for Synthesis: Text entered into the studio or submitted via the API is transmitted to our server to perform phonemization and neural speech generation. Your raw input text is NOT stored in our permanent billing database.`,
          `C. Local History (Browser Storage): The client browser maintains a local history of your recent generations (up to 20 items, including text snippet, voice name, and audio object URL) in localStorage ("kokoro_history"). This data remains on your physical device and can be erased instantly at any time via the "Clear History" button.`,
          `D. Server Logs & Usage Records: Our backend logs standard web request data, including IP address, request method, endpoint path, HTTP status code, and response time. For quota auditing, an internal SQLite record logs: device ID, character count of the request, voice ID, client IP address, and timestamp.`,
          `E. Developer API Keys: If you generate an API key via the Developer portal, a cryptographic key token is stored in the database bound to your anonymous device ID along with a user-assigned label.`,
        ],
      },
      {
        id: 'tts-processing',
        title: '3. Neural TTS Data Processing & AI Privacy',
        content: [
          `On-Premise Model Execution: All speech synthesis is computed directly on our host server infrastructure utilizing the open-weights Kokoro-82M ONNX model and the ONNX Runtime engine.`,
          `No Third-Party AI Data Sharing: Text submitted for synthesis is processed internally by our own Kokoro inference worker. It is NOT submitted, shared, or proxied to external third-party AI model providers or external cloud APIs.`,
          `No Model Training on User Input: Text submitted through the web interface or Developer API is not used to train, fine-tune, or retrain the foundational Kokoro neural model.`,
        ],
      },
      {
        id: 'audio-retention',
        title: '4. Audio & Subtitle Storage and Retention',
        content: [
          `When audio is rendered, the resulting audio file (.mp3 or .wav) and synchronized subtitle file (.srt) are written to a temporary local output directory on the host server filesystem, named with an unguessable randomized UUID.`,
          `Temporary Server Cache: Audio files are stored temporarily on the server disk to enable direct HTTP streaming and downloading via the /audio/{filename} endpoint. Additionally, audio data is delivered directly to your browser as Base64 for instantaneous playback.`,
          `No Long-Term Cloud Archive: We do not archive, replicate, or permanently store your generated audio files in third-party cloud object storage. Server temporary files are subject to routine server-side cleanup. You are encouraged to download your generated audio and subtitle files immediately.`,
        ],
      },
      {
        id: 'cookies-tracking',
        title: '5. Cookies, Local Storage & Analytics',
        content: [
          `HTML5 LocalStorage: We do not use first-party tracking cookies. Instead, we use HTML5 localStorage exclusively for essential functional state: "kokoro_theme" (light/dark preference), "kokoro_device_id" (anonymous quota tracking), "kokoro_history" (your recent audio clips on your device), and "kokoro_api_url" (optional backend server override).`,
          `Infrastructure Security: Our network traffic is protected with edge routing, DDoS mitigation, and SSL termination. Essential security cookies (such as bot-detection cookies) may be used solely to protect the service against malicious traffic.`,
          `No Third-Party Telemetry: We do not employ third-party session recording tools, invasive analytics trackers, or commercial user fingerprinting scripts.`,
          `Google AdSense & Third-Party Advertising: We partner with Google AdSense to serve advertisements when you visit our website. Google and its third-party advertising partners use cookies (including the DoubleClick / DART cookie) to serve ads based on your prior visits to this website or other sites on the internet.`,
          `Opting Out of Personalized Ads: You may opt out of personalized advertising by visiting Google Ads Settings at https://www.google.com/settings/ads. Alternatively, you can opt out of third-party vendor cookies for personalized advertising by visiting http://www.aboutads.info/choices/ or Your Online Choices at https://www.youronlinechoices.com/.`,
        ],
      },
      {
        id: 'payments',
        title: '6. Billing, Payments & Secure Checkout',
        content: [
          `The application provides a complimentary free monthly quota of 30,000 characters per device. Users may optionally upgrade to the Pro Unlimited plan ($9.99/month) or redeem promotional VIP license codes to unlock unlimited character allowances.`,
          `Secure Payment Processing: All subscription payments and credit card transactions are handled exclusively by a certified PCI-DSS Level 1 payment processor. When upgrading, you are redirected to a secure hosted checkout page.`,
          `Zero Card Data Stored: We never collect, transmit, or store your credit card numbers, CVVs, expiration dates, or bank details on our servers. All financial transactions and payment instrument tokens remain strictly within the payment processor's encrypted infrastructure.`,
          `Device-Bound Entitlements: Upon successful payment confirmation via the secure checkout gateway or webhooks, your unique anonymous Device ID is automatically granted Pro Unlimited status without requiring account registration.`,
        ],
      },
      {
        id: 'data-security',
        title: '7. Technical Security Safeguards',
        content: [
          `We implement reasonable and appropriate technical safeguards to protect information against unauthorized access, alteration, or loss. These include HTTPS encryption in transit (via TLS), multi-process isolation for the neural speech worker, randomized non-sequential file naming, and path sanitization to prevent directory traversal attacks.`,
          `However, no method of transmission over the Internet or electronic storage is completely impenetrable. While we strive to protect your data, we cannot guarantee absolute security.`,
        ],
      },
      {
        id: 'user-rights',
        title: '8. User Rights & Data Deletion',
        content: [
          `Local History Deletion: You can instantly delete all audio history and generated text snippets stored in your browser by clicking "Clear History" in the bottom audio player widget.`,
          `Device Identity Reset: You can reset your anonymous device ID at any time by clearing your browser's localStorage or cookies for this site. This immediately severs the association between your browser and prior server quota records.`,
          `Server Record Deletion Requests: Depending on your location and applicable data protection legislation (such as the EU/UK General Data Protection Regulation or the California Consumer Privacy Act/CPRA), you may have the right to request information about or deletion of server logs associated with your IP address or device ID. Such requests may be sent to ${LEGAL_CONFIG.privacyEmail}.`,
        ],
      },
      {
        id: 'children',
        title: '9. Children\'s Privacy',
        content: [
          `Our service is not directed to children under the age of 13 (or under the age of 16 in the European Economic Area and United Kingdom). We do not knowingly collect personal information from children. If you believe a child has provided personal information to us, please contact us at ${LEGAL_CONFIG.privacyEmail} so we can investigate and remove such information.`,
        ],
      },
      {
        id: 'contact',
        title: '10. Changes & Privacy Contact',
        content: [
          `We may update this Privacy Policy from time to time to reflect operational, legal, or technical changes. Any updates will be posted on this page with an updated "Last Updated" date.`,
          `If you have questions, feedback, or privacy-related requests, please contact our privacy contact at ${LEGAL_CONFIG.privacyEmail} or reach out through our project repository at ${LEGAL_CONFIG.githubUrl}.`,
        ],
      },
    ],
  },

  // ==========================================================================
  // 2. TERMS OF SERVICE
  // ==========================================================================
  {
    id: 'terms',
    title: 'Terms of Service',
    shortTitle: 'Terms',
    subtitle: 'Governing agreement for accessing Kokoro Voice Studio, commercial licensing, voice usage, and disclaimers.',
    iconName: 'FileText',
    effectiveDate: LEGAL_CONFIG.effectiveDate,
    lastUpdated: LEGAL_CONFIG.lastUpdated,
    sections: [
      {
        id: 'acceptance',
        title: '1. Acceptance of Terms & Eligibility',
        content: [
          `By accessing or using ${LEGAL_CONFIG.serviceName} (the "Service"), you agree to be bound by these Terms of Service ("Terms") and our Acceptable Use Policy. If you do not agree to these Terms, you must not access or use the Service.`,
          `You must be at least 13 years of age (or the minimum legal age of digital consent in your jurisdiction) to use the Service. If you are using the Service on behalf of a business, company, or legal entity, you represent and warrant that you have full authority to bind that entity to these Terms.`,
        ],
      },
      {
        id: 'service-description',
        title: '2. Description of Service & Architecture',
        content: [
          `${LEGAL_CONFIG.serviceName} is an artificial intelligence-powered text-to-speech platform and digital audio workstation. The Service provides access to neural speech synthesis across multiple languages, acoustic EQ mastering presets, and synchronized subtitle (.srt) generation powered by the Kokoro-82M neural model.`,
          `The Service is delivered through web interfaces, optional desktop distributions, and developer API endpoints. Access is provided on an "as is" and "as available" basis.`,
        ],
      },
      {
        id: 'user-access-accounts',
        title: '3. Device-Based Access & Anonymous Identifiers',
        content: [
          `The Service utilizes an anonymous device identifier architecture. You are not required to maintain an authenticated user account with a password. Your device identifier ("Device ID") is generated in your browser and used to calculate monthly character consumption.`,
          `You are responsible for maintaining the confidentiality of any Developer API keys generated under your Device ID. You agree to notify us immediately of any unauthorized use of your API keys.`,
        ],
      },
      {
        id: 'quotas-usage',
        title: '4. Character Quotas, Free Tier & Pro Features',
        content: [
          `Free Tier: Each device receives a complimentary quota of 30,000 characters per calendar month. This character allocation automatically resets on the first day of each UTC calendar month. Unused characters do not roll over.`,
          `Pro Tier: Devices with an active Pro status (unlocked via promotional passcodes, VIP keys, or authorized licenses) receive unlimited character generation subject to fair use and system stability requirements.`,
          `Quota Calculation: Quotas are decremented based on the character length of the input text submitted in each synthesis request. We reserve the right to modify quota limits and usage tiers at our discretion.`,
        ],
      },
      {
        id: 'api-access',
        title: '5. Developer API & Rate Limits',
        content: [
          `Developer API keys are provided to programmatically access speech synthesis endpoints (including OpenAI-compatible audio speech endpoints).`,
          `API usage is subject to automated rate limits to prevent denial-of-service abuse and maintain infrastructure availability. Circumventing rate limits, forging request headers, or generating parallel requests that disrupt service operations is strictly prohibited.`,
        ],
      },
      {
        id: 'billing-subscriptions',
        title: '6. Billing, Subscriptions & Promotional Codes',
        content: [
          `Pro Subscriptions: Users may subscribe to Kokoro Voice Studio Pro Unlimited for $9.99 USD per month. Subscriptions automatically renew on a monthly basis until cancelled.`,
          `Payment Terms: Payments are processed securely via our certified payment gateway. By subscribing, you authorize our payment processor to charge your chosen payment method the applicable recurring monthly fee until you cancel.`,
          `Promotional Codes: Promotional and VIP license codes may be provided for beta testing, promotional events, or contributor access. We reserve the right to revoke promotional codes that are compromised, abused, or distributed in violation of their intended terms.`,
          `Subscription Management & Cancellation: You may cancel your subscription at any time. Upon cancellation, your Pro Unlimited access remains active until the end of the current paid billing cycle.`,
        ],
      },
      {
        id: 'user-input-rights',
        title: '7. Rights in User-Submitted Input',
        content: [
          `You retain all pre-existing intellectual property rights and ownership in the text, scripts, lyrics, or written materials that you submit to the Service ("User Input").`,
          `By submitting User Input, you grant ${LEGAL_CONFIG.serviceName} a strictly limited, worldwide, non-exclusive, royalty-free license to process, phonemize, and synthesize that text solely for the purpose of generating your requested speech audio and subtitle outputs.`,
          `You represent and warrant that you possess all necessary rights, licenses, and permissions to submit your User Input and that your input does not violate third-party intellectual property, privacy, or publicity rights.`,
        ],
      },
      {
        id: 'generated-audio-rights',
        title: '8. Rights, Permissions & Ownership in Generated Audio',
        content: [
          `Distinction of Ownership & Commercial Permissions: ${LEGAL_CONFIG.serviceName} claims no proprietary copyright ownership over the synthetic audio files (.mp3, .wav) or subtitle files (.srt) generated from your lawful User Input.`,
          `Commercial Exploitation License: Subject to your full compliance with these Terms and the Acceptable Use Policy, we grant you a perpetual, worldwide, non-exclusive, royalty-free, transferable license to use, reproduce, modify, distribute, publicly perform, broadcast, synchronize, and commercially monetize generated audio files (such as in YouTube videos, podcasts, video games, audiobooks, TikToks, and commercials).`,
          `Jurisdictional Copyright Status: You acknowledge that the legal status of artificial intelligence-generated outputs varies across jurisdictions. In many jurisdictions (such as under United States Copyright Office guidance), machine-generated outputs produced without sufficient creative human authorship may not be eligible for statutory copyright registration. We make no warranty that generated audio can be registered as a copyrighted work in any jurisdiction.`,
          `Responsibility for Output: You are solely and completely responsible for your use, distribution, and publication of generated audio files and subtitles, including ensuring that your use does not violate right-of-publicity laws, defamation statutes, or trademark protections.`,
        ],
      },
      {
        id: 'open-source-models',
        title: '9. Kokoro Model & Open-Source Attribution',
        content: [
          `The core speech generation engine utilizes the open-weights Kokoro-82M neural architecture created by hexgrad and released under the Apache 2.0 license, alongside open-source acoustic and G2P libraries.`,
          `Nothing in these Terms conveys proprietary ownership of the underlying open-source model weights or foundational runtime engines to you or to ${LEGAL_CONFIG.serviceName}. Your use of the model weights is governed by their applicable open-source licenses.`,
        ],
      },
      {
        id: 'voice-restrictions',
        title: '10. Voice Usage & Impersonation Prohibitions',
        content: [
          `Synthetic Voices: All voices provided in the catalog are synthetic character voices produced by neural speech models.`,
          `Prohibited Impersonation: You may not use the Service to generate voice audio intended to deceptively impersonate any living individual, celebrity, political candidate, public official, law enforcement agent, or corporate representative without their express, verifiable, written authorization.`,
          `Voice Availability: We reserve the right to add, modify, re-tune, or discontinue specific synthetic voices from the catalog at any time without prior notice.`,
        ],
      },
      {
        id: 'service-availability',
        title: '11. Service Availability & Modifications',
        content: [
          `We strive to maintain high availability; however, we do not guarantee uninterrupted, error-free, or 100% uptime. The Service may be temporarily unavailable due to maintenance, system upgrades, hardware failures, or network outages.`,
          `We reserve the right to modify, suspend, or discontinue any aspect of the Service, including quotas, API endpoints, or features, at any time with or without notice.`,
        ],
      },
      {
        id: 'disclaimers',
        title: '12. Warranty Disclaimers',
        content: [
          `THE SERVICE IS PROVIDED ON AN "AS IS" AND "AS AVAILABLE" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE, AND NON-INFRINGEMENT.`,
          `WE DO NOT WARRANT THAT THE SERVICE WILL MEET YOUR REQUIREMENTS, BE UNINTERRUPTED, ACCURATE, SECURE, OR ERROR-FREE, OR THAT DEFECTS WILL BE CORRECTED. SPEECH SYNTHESIS OUTPUTS MAY OCCASIONALLY CONTAIN PRONUNCIATION INACCURACIES, ACOUSTIC ARTIFACTS, OR UNEXPECTED INFLECTIONS.`,
        ],
      },
      {
        id: 'liability',
        title: '13. Limitation of Liability',
        content: [
          `TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, IN NO EVENT SHALL ${LEGAL_CONFIG.serviceName.toUpperCase()}, ITS OPERATORS, CONTRIBUTORS, OR AFFILIATES BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, EXEMPLARY, OR PUNITIVE DAMAGES, INCLUDING DAMAGES FOR LOSS OF PROFITS, REVENUE, GOODWILL, DATA, OR BUSINESS INTERRUPTION, ARISING OUT OF OR IN CONNECTION WITH YOUR USE OR INABILITY TO USE THE SERVICE.`,
          `OUR TOTAL AGGREGATE LIABILITY ARISING OUT OF OR RELATED TO THESE TERMS OR THE SERVICE SHALL NOT EXCEED THE GREATER OF (A) THE TOTAL AMOUNT ACTUALLY PAID BY YOU TO US FOR THE SERVICE IN THE TWELVE (12) MONTHS PRECEDING THE EVENT GIVING RISE TO LIABILITY, OR (B) FIFTY UNITED STATES DOLLARS ($50.00 USD).`,
        ],
      },
      {
        id: 'indemnification',
        title: '14. Indemnification',
        content: [
          `You agree to defend, indemnify, and hold harmless ${LEGAL_CONFIG.serviceName}, its operators, contributors, and licensors from and against any claims, liabilities, damages, losses, costs, or expenses (including reasonable attorneys' fees) arising out of or related to: (a) your User Input; (b) your use or commercial exploitation of generated audio or subtitles; (c) your violation of these Terms or the Acceptable Use Policy; or (d) your violation of any third-party rights, including intellectual property, privacy, or publicity rights.`,
        ],
      },
      {
        id: 'termination',
        title: '15. Suspension & Termination',
        content: [
          `We may suspend or terminate your access to the Service, including revoking your API keys and blocking your Device ID or IP address, immediately and without prior notice if we determine that you have violated these Terms, the Acceptable Use Policy, or any applicable law.`,
          `Upon termination, all licenses granted to you regarding the active use of the Service shall immediately cease; however, provisions that by their nature should survive termination (including intellectual property provisions, disclaimers, limitations of liability, and indemnification) will remain in effect.`,
        ],
      },
      {
        id: 'governing-law',
        title: '16. Governing Law & Dispute Resolution',
        content: [
          `These Terms shall be governed by and construed in accordance with the laws of ${LEGAL_CONFIG.governingLaw}, without regard to its conflict of law principles.`,
          `Any dispute, controversy, or claim arising out of or relating to these Terms or the Service shall be submitted to the competent courts of ${LEGAL_CONFIG.governingLaw}, unless mandatory local consumer protection statutes mandate alternative dispute resolution.`,
        ],
      },
      {
        id: 'general',
        title: '17. Miscellaneous & Contact',
        content: [
          `Severability: If any provision of these Terms is found to be unlawful, void, or unenforceable, that provision shall be deemed severable and shall not affect the validity and enforceability of any remaining provisions.`,
          `Entire Agreement: These Terms, together with our Privacy Policy and Acceptable Use Policy, constitute the entire agreement between you and ${LEGAL_CONFIG.serviceName} regarding your use of the Service.`,
          `Contact: For inquiries regarding these Terms, please contact ${LEGAL_CONFIG.supportEmail} or our project repository at ${LEGAL_CONFIG.githubUrl}.`,
        ],
      },
    ],
  },

  // ==========================================================================
  // 3. ACCEPTABLE USE POLICY
  // ==========================================================================
  {
    id: 'acceptable-use',
    title: 'Acceptable Use Policy',
    shortTitle: 'Acceptable Use',
    subtitle: 'Standards of conduct, prohibited activities, abuse prevention, and voice generation safety guidelines.',
    iconName: 'AlertTriangle',
    effectiveDate: LEGAL_CONFIG.effectiveDate,
    lastUpdated: LEGAL_CONFIG.lastUpdated,
    sections: [
      {
        id: 'purpose',
        title: '1. Purpose & Scope',
        content: [
          `This Acceptable Use Policy ("AUP") defines the mandatory standards of conduct governing all users of ${LEGAL_CONFIG.serviceName}, including our web application, desktop software, and developer APIs.`,
          `Our mission is to empower creative voice generation, video narration, accessibility reading, and game development. We strictly prohibit the use of our infrastructure for malicious, fraudulent, deceptive, or abusive activities.`,
        ],
      },
      {
        id: 'illegal-harmful',
        title: '2. Prohibited Illegal & Harmful Activities',
        content: [
          `You may not use the Service to generate, transmit, or distribute audio or content that:`,
          `• Violates any applicable local, national, or international law, regulation, or ordinance.`,
          `• Constitutes or promotes illegal financial fraud, wire fraud, bank scams, pyramid schemes, or phishing operations.`,
          `• Facilitates harassment, stalking, cyberbullying, physical threats, intimidation, or intentional infliction of emotional distress.`,
          `• Promotes or incites violence, acts of terrorism, hate speech, or discrimination based on race, ethnicity, religion, disability, age, gender identity, or sexual orientation.`,
          `• Facilitates the exploitation or endangerment of minors in any form.`,
          `• Disseminates malware, spyware, ransomware, trojans, or malicious payloads.`,
        ],
      },
      {
        id: 'deceptive-impersonation',
        title: '3. Prohibited Impersonation & Deceptive Media',
        content: [
          `The realistic nature of neural speech synthesis requires strict adherence to ethical standards. You may not:`,
          `• Generate synthetic speech intended to deceptively impersonate any living individual, celebrity, political figure, government official, or corporate executive without their explicit, verifiable, written authorization.`,
          `• Use the Service to execute social engineering attacks, CEO fraud, emergency family scams ("grandparent scams"), or credential harvesting.`,
          `• Produce deceptive political deepfakes, election interference robocalls, or fraudulent disinformation campaigns designed to mislead voters or the public regarding election procedures or official declarations.`,
          `• Generate synthetic voice recordings to falsify legal evidence, fabricate sworn testimony, or mislead law enforcement or judicial authorities.`,
        ],
      },
      {
        id: 'voice-cloning-rules',
        title: '4. Voice Rights & Likeness Consent',
        content: [
          `• You must possess lawful rights, licenses, or explicit consent before utilizing voice characteristics to imitate an identifiable real-world individual.`,
          `• The platform reserves the right to suspend or ban any device or API key found to be engaged in non-consensual voice likeness exploitation.`,
          `• We encourage creators utilizing synthetic audio in public broadcasts, journalistic reporting, or political commentary to include clear attribution or disclosure (such as "Audio synthesized with AI") to promote transparency.`,
        ],
      },
      {
        id: 'infrastructure-abuse',
        title: '5. System Integrity, API & Resource Abuse',
        content: [
          `To protect infrastructure availability and ensure equitable access for all users, you agree not to:`,
          `• Attempt to circumvent, tamper with, or reset monthly character quota limits, including manipulating the "X-Device-Id" header, spoofing IP addresses, or cycling proxy networks.`,
          `• Launch denial-of-service (DoS/DDoS) attacks, automated stress-testing scripts, or floods of concurrent synthesis requests designed to degrade server responsiveness.`,
          `• Reverse engineer, decompile, or disassemble proprietary backend routing mechanisms, except to the extent permitted by underlying open-source component licenses.`,
          `• Probe, scan, or test the vulnerability of our servers, networks, or endpoints without prior written authorization.`,
          `• Share, publish, or sell API keys to unauthorized third parties in violation of rate limits.`,
        ],
      },
      {
        id: 'enforcement',
        title: '6. Monitoring, Investigation & Enforcement',
        content: [
          `We do not routinely monitor the semantic content of all user audio generations in real-time; however, we monitor system throughput, rate limits, and error patterns for abuse detection.`,
          `We reserve the right to investigate reported violations of this policy. If a violation is substantiated, we may take immediate action, including issuing warnings, terminating API keys, blocking Device IDs, blacklisting IP subnets, and reporting unlawful conduct to relevant legal authorities.`,
          `Reports of abuse may be submitted directly to our designated safety channel at ${LEGAL_CONFIG.abuseEmail}.`,
        ],
      },
    ],
  },

  // ==========================================================================
  // 4. AI & VOICE POLICY
  // ==========================================================================
  {
    id: 'ai-policy',
    title: 'AI & Voice Ethics Policy',
    shortTitle: 'AI & Voice',
    subtitle: 'Principles governing synthetic neural speech, model transparency, voice catalog standards, and synthetic media disclosure.',
    iconName: 'Sparkles',
    effectiveDate: LEGAL_CONFIG.effectiveDate,
    lastUpdated: LEGAL_CONFIG.lastUpdated,
    sections: [
      {
        id: 'nature-of-ai',
        title: '1. Nature of Synthetic Neural Speech',
        content: [
          `All audio synthesized by ${LEGAL_CONFIG.serviceName} is artificial intelligence-generated speech produced by deep neural networks. Voices are computed algorithmically from phonetic and mathematical representations rather than real-time human studio recordings.`,
          `While modern neural models produce natural-sounding speech with expressive cadence and human-like intonation, outputs may occasionally exhibit acoustic anomalies, mispronunciations of rare words or acronyms, or unintended prosodic inflections. Users are advised to review generated speech before publishing it in critical contexts.`,
        ],
      },
      {
        id: 'transparency-disclosure',
        title: '2. Transparency & Synthetic Media Disclosure',
        content: [
          `We advocate for the responsible, ethical, and transparent deployment of synthetic voice technology across society.`,
          `Recommended Labeling: When generated speech is published in journalism, documentary filmmaking, political discourse, educational content, or customer support automation, we strongly recommend disclosing that the audio was generated with artificial intelligence (e.g., using visual labels, audio disclaimers, or platform-standard "AI-generated" metadata tags).`,
          `Deceptive Contexts Prohibited: Synthetic audio must never be presented as an unedited, authentic recording of a real individual in any context where doing so would mislead listeners, defame a person, or deceive the public.`,
        ],
      },
      {
        id: 'model-provenance',
        title: '3. Model Architecture & Open Research Provenance',
        content: [
          `The foundational speech synthesis architecture utilized by the Service is Kokoro-82M ONNX, an efficient 82-million parameter neural model created by hexgrad and released under the permissive Apache 2.0 open-source license.`,
          `Grapheme-to-phoneme (G2P) conversion is powered by open-source multilingual phonetic engines including eSpeak-NG and customized language-specific phonemizers.`,
          `We believe in accessible, transparent voice technology that operates efficiently on standard CPU hardware without proprietary cloud vendor lock-in.`,
        ],
      },
      {
        id: 'voice-catalog-standards',
        title: '4. Voice Catalog Standards & Adjustments',
        content: [
          `Our catalog currently provides 60 international voices spanning 9+ global languages (including American and British English, French, Japanese, Korean, Mandarin Chinese, Spanish, Hindi, Italian, and Brazilian Portuguese).`,
          `Each voice profile represents a distinct synthetic acoustic character profile (e.g., Bella, Adam, Minji, Camille, Xiaoxiao).`,
          `Voice Catalog Evolution: Voice models and weights may be updated, retrained, tuned, or retired to enhance pronunciation quality, improve acoustic naturalness, address community feedback, or comply with legal and ethical standards. We do not guarantee permanent, unchanging availability of any single voice checkpoint.`,
        ],
      },
      {
        id: 'blender-ethics',
        title: '5. Neural Voice Blender Ethics',
        content: [
          `The platform provides a Neural Voice Blender that mathematically interpolates between existing voice weight vectors to produce hybrid character timbres.`,
          `Users may not use voice interpolation techniques to deliberately approximate or reverse-engineer the unique voice identity of living individuals without consent.`,
        ],
      },
      {
        id: 'safety-commitment',
        title: '6. Safety, Moderation & Contact',
        content: [
          `We reserve the right to restrict or disable synthesis of content that threatens individual safety, violates rights of publicity, or promotes hate speech.`,
          `If you have questions regarding our voice technology or wish to report a safety concern regarding a specific synthetic voice, please contact ${LEGAL_CONFIG.abuseEmail}.`,
        ],
      },
    ],
  },

  // ==========================================================================
  // 5. COOKIE POLICY
  // ==========================================================================
  {
    id: 'cookies',
    title: 'Cookie & Storage Policy',
    shortTitle: 'Cookies & Storage',
    subtitle: 'Detailed technical disclosures regarding HTML5 localStorage, edge infrastructure cookies, and advertising status.',
    iconName: 'Cookie',
    effectiveDate: LEGAL_CONFIG.effectiveDate,
    lastUpdated: LEGAL_CONFIG.lastUpdated,
    sections: [
      {
        id: 'introduction',
        title: '1. Introduction to Cookies & Client Storage',
        content: [
          `This Cookie & Storage Policy explains how ${LEGAL_CONFIG.serviceName} uses browser storage technologies, including HTTP cookies and HTML5 localStorage.`,
          `We distinguish technically between HTTP cookies (small text files sent back and forth between browser and server on every HTTP request) and HTML5 localStorage (client-side key-value storage residing strictly on your local device that is not sent in HTTP headers).`,
        ],
      },
      {
        id: 'first-party-cookies',
        title: '2. First-Party Tracking Cookies: None',
        content: [
          `Zero Tracking Cookies: ${LEGAL_CONFIG.serviceName} does NOT set any first-party advertising, commercial profiling, or tracking cookies on your device.`,
          `We do not use tracking pixels, fingerprinting beacons, or behavioral tracking scripts.`,
        ],
      },
      {
        id: 'localstorage',
        title: '3. Essential HTML5 LocalStorage Usage',
        content: [
          `The application utilizes HTML5 localStorage solely for essential functional and UI operations. The specific keys utilized are:`,
          `• "kokoro_theme": Stores your visual display preference ("light" or "dark"). Stored locally on your device indefinitely until cleared.`,
          `• "kokoro_device_id": Stores your random anonymous device identifier (e.g., "dev_web_xxxxxxxxxxxxxxxx"). Used to query and track your monthly character quota and associate Developer API keys.`,
          `• "kokoro_history": Stores a local JSON array of your up to 20 most recent speech generations (titles, timestamps, audio object URLs, and subtitle texts) on your device. You can erase this data at any time via the "Clear History" button.`,
          `• "kokoro_api_url": Stores an optional custom backend server URL if you choose to configure a custom endpoint via developer configuration.`,
          `LocalStorage data never leaves your browser unless an identifier is transmitted in request headers (e.g., X-Device-Id) to perform a requested server action.`,
        ],
      },
      {
        id: 'infrastructure-cookies',
        title: '4. Third-Party Edge & Infrastructure Cookies (Cloudflare)',
        content: [
          `Our domain is routed through Cloudflare to provide DDoS mitigation, edge caching, and web application firewall security.`,
          `Cloudflare may place essential security cookies (such as "__cf_bm" or "cf_clearance") in your browser. These cookies are strictly necessary to identify trusted web traffic, mitigate malicious botnets, and ensure network security. They do not track your personal identity or browsing behavior across unrelated websites.`,
        ],
      },
      {
        id: 'advertising-adsense',
        title: '5. Google AdSense & Third-Party Advertising Cookies',
        content: [
          `Google AdSense Integration: ${LEGAL_CONFIG.serviceName} uses Google AdSense and third-party advertising networks to serve advertisements across our website to keep our neural text-to-speech services free for creators worldwide.`,
          `How Advertising Cookies Work: Third-party vendors, including Google, use cookies to serve ads based on a user's prior visits to our website or other websites. Google's use of advertising cookies enables it and its partners to serve ads to our users based on their visit to our sites and/or other sites on the Internet.`,
          `DoubleClick / DART Cookie: The DoubleClick DART cookie is used by Google in the ads served on publisher websites displaying AdSense for content ads. When users visit our website and view or click an ad, a cookie may be placed in their browser cache.`,
          `User Privacy & Opt-Out Controls: You have full control over personalized advertising preferences:`,
          `• Opt-Out via Google: You may opt out of personalized advertising by visiting Google Ads Settings (https://www.google.com/settings/ads).`,
          `• Opt-Out via Industry Portals: You can opt out of third-party vendor cookies for personalized advertising by visiting the Digital Advertising Alliance at http://www.aboutads.info/choices/ or Your Online Choices (EU/UK) at https://www.youronlinechoices.com/.`,
          `• Browser-Level Cookie Blocking: You can configure your browser to reject all third-party cookies. Disabling cookies will not restrict or disable your ability to synthesize speech on Kokoro Voice Studio.`,
        ],
      },
      {
        id: 'managing-storage',
        title: '6. How to Manage and Clear Storage',
        content: [
          `You can control, review, and clear browser cookies and localStorage data at any time through your browser settings:`,
          `• Chrome: Settings → Privacy and Security → Site settings → Cookies and site data.`,
          `• Firefox: Settings → Privacy & Security → Cookies and Site Data.`,
          `• Safari: Preferences → Privacy → Manage Website Data.`,
          `• Edge: Settings → Cookies and site permissions.`,
          `Please note that clearing localStorage will reset your theme preference and generate a new anonymous Device ID upon your next visit.`,
        ],
      },
    ],
  },

  // ==========================================================================
  // 6. COPYRIGHT / DMCA POLICY
  // ==========================================================================
  {
    id: 'dmca',
    title: 'Copyright & DMCA Policy',
    shortTitle: 'Copyright / DMCA',
    subtitle: 'Copyright protection standards, takedown notice guidelines, counter-notification procedure, and designated agent information.',
    iconName: 'Scale',
    effectiveDate: LEGAL_CONFIG.effectiveDate,
    lastUpdated: LEGAL_CONFIG.lastUpdated,
    sections: [
      {
        id: 'respect-for-ip',
        title: '1. Respect for Intellectual Property',
        content: [
          `${LEGAL_CONFIG.serviceName} respects the intellectual property rights of authors, creators, and copyright owners. We expect all users of our Service to respect third-party copyrights as well.`,
          `Users are solely responsible for ensuring that they hold the necessary rights, licenses, or fair-use justifications for any text, scripts, or materials they submit to the Service for speech synthesis.`,
        ],
      },
      {
        id: 'notice-procedure',
        title: '2. Submitting a DMCA Takedown Notice',
        content: [
          `If you are a copyright owner or authorized representative and believe that content accessible through ${LEGAL_CONFIG.serviceName} infringes your copyrighted work, you may submit a formal notification pursuant to the Digital Millennium Copyright Act (17 U.S.C. § 512(c)) containing the following information:`,
          `1. A physical or electronic signature of a person authorized to act on behalf of the owner of an exclusive right that is allegedly infringed.`,
          `2. Identification of the copyrighted work claimed to have been infringed (e.g., title, author, registration number, or URL of original publication).`,
          `3. Identification of the material claimed to be infringing and information reasonably sufficient to permit us to locate the material (e.g., specific audio URL, filename, or API endpoint).`,
          `4. Your contact information, including your full legal name, physical address, telephone number, and email address.`,
          `5. A statement that you have a good faith belief that use of the material in the manner complained of is not authorized by the copyright owner, its agent, or the law.`,
          `6. A statement that the information in the notification is accurate, and under penalty of perjury, that you are authorized to act on behalf of the owner of an exclusive right that is allegedly infringed.`,
        ],
      },
      {
        id: 'designated-agent',
        title: '3. Designated Copyright Contact',
        content: [
          `Formal copyright notices should be transmitted to our designated copyright contact:`,
          `• Designated Contact: ${LEGAL_CONFIG.companyName} — DMCA Department`,
          `• Email: ${LEGAL_CONFIG.dmcaEmail}`,
          `• Physical Address: ${LEGAL_CONFIG.legalAddress}`,
          `• Project Repository: ${LEGAL_CONFIG.githubUrl}`,
          `Notifications containing missing or insufficient information may delay our ability to process the request.`,
        ],
      },
      {
        id: 'counter-notice',
        title: '4. Counter-Notification Procedure',
        content: [
          `If you believe that your content was removed or disabled as a result of a mistake or misidentification, you may submit a written counter-notification containing:`,
          `1. Your physical or electronic signature.`,
          `2. Identification of the material that was removed or disabled and the location where it appeared before removal.`,
          `3. A statement under penalty of perjury that you have a good faith belief that the material was removed or disabled as a result of mistake or misidentification.`,
          `4. Your name, address, telephone number, and a statement that you consent to the jurisdiction of the federal district court for your judicial district (or, if outside the United States, for any judicial district in which the service provider may be found).`,
        ],
      },
      {
        id: 'repeat-infringer',
        title: '5. Repeat Infringer Policy',
        content: [
          `In accordance with applicable law, we maintain a policy of terminating API keys and blocking Device IDs of users who are determined to be repeat copyright infringers.`,
        ],
      },
    ],
  },

  // ==========================================================================
  // 7. REFUND & CANCELLATION POLICY
  // ==========================================================================
  {
    id: 'refunds',
    title: 'Refund & Cancellation Policy',
    shortTitle: 'Refunds & Cancellation',
    subtitle: 'Subscription billing terms, cancellation policy, character quota limits, promotional passes, and refund guidelines.',
    iconName: 'RefreshCw',
    effectiveDate: LEGAL_CONFIG.effectiveDate,
    lastUpdated: LEGAL_CONFIG.lastUpdated,
    sections: [
      {
        id: 'current-status',
        title: '1. Secure Payment Processing & Encryption',
        content: [
          `Secure Recurring Subscriptions: Kokoro Voice Studio offers an optional Pro Unlimited subscription ($9.99/month) securely processed through a certified PCI-DSS Level 1 payment gateway.`,
          `Zero Payment Data Stored: We do not process, collect, or store payment card details, bank account numbers, or billing addresses on our servers. All payment handling is conducted directly under PCI-DSS Level 1 security standards.`,
          `Seamless Anonymous Upgrades: Subscriptions are tied directly to your unique anonymous Device ID so you can enjoy unlimited speech synthesis without filling out account registration forms.`,
        ],
      },
      {
        id: 'free-quota-terms',
        title: '2. Free Monthly Quotas & Reset Rules',
        content: [
          `Every device receives a complimentary quota of 30,000 characters per calendar month.`,
          `Monthly Reset: Quota usage resets automatically on the first day of each UTC calendar month. Unused characters from a prior month do not carry forward, accrue, or convert to cash equivalents.`,
        ],
      },
      {
        id: 'promo-codes',
        title: '3. Promotional & VIP License Passes',
        content: [
          `Users who obtain a promotional VIP key or license passcode (such as alpha tester passes or community promotional codes) may redeem it in the application to unlock unlimited Pro character allowances.`,
          `Promotional codes are granted free of charge or as part of authorized beta programs. They have no cash redemption value, are non-transferable unless explicitly specified, and may be modified or revoked in cases of system abuse or fraudulent distribution.`,
        ],
      },
      {
        id: 'subscription-billing',
        title: '4. Pro Subscription Billing, Cancellation & Refunds',
        content: [
          `Monthly Subscription Terms: Kokoro Voice Studio Pro is billed at $9.99 USD per month in advance on a recurring monthly schedule.`,
          `• Subscription Cancellation: You may cancel recurring billing at any time by contacting our support team or through your payment link. Upon cancellation, your Pro benefits remain active until the end of the paid billing month.`,
          `• 14-Day Refund Evaluation: If you experience persistent technical defects, service interruptions, or unintended billing, you may request a refund within fourteen (14) days of the billing charge by reaching out to support with your Device ID or checkout confirmation.`,
          `• Failed Renewals: If a scheduled recurring payment cannot be completed, access will gracefully return to the standard free monthly tier (30,000 characters/month).`,
        ],
      },
      {
        id: 'billing-inquiries',
        title: '5. Billing & Quota Support',
        content: [
          `If you have questions regarding your character quota, promotional key redemption, or upcoming commercial plans, please contact our support team at ${LEGAL_CONFIG.supportEmail}.`,
        ],
      },
    ],
  },

  // ==========================================================================
  // 8. ABOUT US
  // ==========================================================================
  {
    id: 'about',
    title: 'About Kokoro Voice Studio',
    shortTitle: 'About Us',
    subtitle: 'Our mission, technology, audio workstation capabilities, and open-source foundation.',
    iconName: 'Info',
    effectiveDate: LEGAL_CONFIG.effectiveDate,
    lastUpdated: LEGAL_CONFIG.lastUpdated,
    sections: [
      {
        id: 'mission',
        title: '1. What is Kokoro Voice Studio?',
        content: [
          `${LEGAL_CONFIG.serviceName} is a modern, high-performance artificial intelligence text-to-speech workstation engineered to make realistic neural voice generation accessible, fast, and privacy-respecting.`,
          `Traditional cloud TTS platforms are often locked behind expensive paywalls, complex subscription tiers, proprietary lock-in, and strict character metering. Kokoro Voice Studio solves this problem by packaging cutting-edge open-weights neural speech synthesis into an intuitive, studio-grade web and desktop workstation.`,
        ],
      },
      {
        id: 'technology',
        title: '2. Architecture & Neural Speech Technology',
        content: [
          `At the heart of the platform is Kokoro-82M ONNX, an ultra-compact and highly capable 82-million parameter neural text-to-speech model.`,
          `• CPU-Optimized Inference: Synthesizes high-fidelity speech faster than real-time on standard server and desktop CPUs without requiring high-end dedicated GPUs.`,
          `• 60 Studio Voices Across 9+ Languages: Natural character narration in American English, British English, French, Japanese, Korean, Mandarin Chinese, Spanish, Hindi, Italian, and Brazilian Portuguese.`,
          `• Multilingual Phonemization: Advanced script-aware grapheme-to-phoneme (G2P) conversion accurately preserving accents, CJK ideographs, Hangul, and Devanagari script.`,
          `• Acoustic Studio EQ Mastering: Built-in DSP mastering presets (including Bass Boost, Radio Punch, Cinematic Trailer, and Vintage Tube) tailored for video editors, podcasters, and content creators.`,
          `• Synchronized Subtitle Generator: Automatically calculates word pacing and exports synchronized .srt and .vtt subtitle files formatted for CapCut, Premiere Pro, and DaVinci Resolve.`,
        ],
      },
      {
        id: 'philosophy',
        title: '3. Product & Privacy Philosophy',
        content: [
          `We believe great creative software should respect user privacy and creative autonomy:`,
          `• Zero-Login Simplicity: No required accounts, passwords, or tracking cookies for general use.`,
          `• Local Data Ownership: Your generation history stays on your computer's browser storage.`,
          `• Open Standards & Developer Freedom: Full OpenAI-compatible speech synthesis API endpoints allowing developers to plug Kokoro Voice Studio directly into existing applications.`,
        ],
      },
      {
        id: 'open-source',
        title: '4. Open-Source Roots & Project Heritage',
        content: [
          `${LEGAL_CONFIG.serviceName} is developed as an open-source project by Dilshan Chandrarathne and open-source contributors.`,
          `The complete source code, desktop build scripts, and issue tracking are maintained publicly on GitHub at ${LEGAL_CONFIG.githubUrl}. We invite developers, audio engineers, and accessibility advocates to review our code, report bugs, and contribute improvements.`,
        ],
      },
    ],
  },

  // ==========================================================================
  // 9. CONTACT US
  // ==========================================================================
  {
    id: 'contact',
    title: 'Contact Directory & Support',
    shortTitle: 'Contact Us',
    subtitle: 'Official communication channels for general support, privacy inquiries, DMCA notices, and developer partnerships.',
    iconName: 'Mail',
    effectiveDate: LEGAL_CONFIG.effectiveDate,
    lastUpdated: LEGAL_CONFIG.lastUpdated,
    sections: [
      {
        id: 'channels',
        title: '1. Departmental Contact Channels',
        content: [
          `To ensure your inquiry is routed to the appropriate department, please use the designated communication channels below:`,
          `• General Support & Feedback: ${LEGAL_CONFIG.supportEmail}`,
          `  For general application questions, quota assistance, feature suggestions, or user feedback.`,
          `• Privacy & Data Requests: ${LEGAL_CONFIG.privacyEmail}`,
          `  For inquiries regarding our Privacy Policy, data deletion requests, or regulatory privacy questions.`,
          `• Copyright & DMCA Takedown Notices: ${LEGAL_CONFIG.dmcaEmail}`,
          `  For formal intellectual property infringement notices and counter-notifications.`,
          `• Abuse & Safety Reports: ${LEGAL_CONFIG.abuseEmail}`,
          `  For reporting suspected violations of our Acceptable Use Policy, non-consensual voice cloning, or deceptive media.`,
          `• Developer & API Partnerships: ${LEGAL_CONFIG.apiEmail}`,
          `  For inquiries regarding high-volume API keys, self-hosted deployments, or commercial integration assistance.`,
        ],
      },
      {
        id: 'community-github',
        title: '2. Community & GitHub Issue Tracker',
        content: [
          `For public bug reports, desktop installer questions, feature requests, or developer discussions, please visit our official GitHub repository:`,
          `• Official Repository: ${LEGAL_CONFIG.githubUrl}`,
          `• Issues & Bug Reports: ${LEGAL_CONFIG.githubUrl}/issues`,
          `• Releases & Desktop Binaries: ${LEGAL_CONFIG.githubUrl}/releases`,
        ],
      },
      {
        id: 'response-times',
        title: '3. Response Expectations',
        content: [
          `Our support team reviews inquiries in the order they are received. We aim to respond to standard inquiries within 24 to 48 business hours. Priority is given to verified security disclosures and formal copyright notices.`,
        ],
      },
    ],
  },
];

export function getLegalDoc(id: LegalDocId | string): LegalDocument | undefined {
  return ALL_LEGAL_DOCS.find((doc) => doc.id === id);
}
