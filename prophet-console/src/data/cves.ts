/**
 * CVE records used by the Prophet operator console.
 *
 * The 5 canonical entries (Log4Shell, Struts, Heartbleed, Zerologon, Pulse
 * Secure) are enriched with KEV metadata extracted at build time from
 * kve.json. The full kve.json (1.3 MB, 1587 entries) is NOT bundled at
 * runtime — only the 5 matching rows are inlined here.
 *
 * Log4Shell maps to the active edge-appliance demo candidate.
 * The other four carry null worldCandidateId for now.
 */

export interface CVERecord {
  rank: number;
  cveId: string;
  vendor: string;
  product: string;
  description: string;
  cvss: number;
  cvssLabel: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  epss: number;
  nuclei: boolean;
  exploitDb: boolean;
  attackTechnique: string;
  cwe: string;
  vulnClass: string;
  // World-Side linkage
  worldCandidateId: string | null;
  // KEV metadata (extracted from kve.json)
  kevDateAdded: string;
  kevSourceProduct: string;
  kevDescription: string;
}

export const cves: CVERecord[] = [
  {
    rank: 1,
    cveId: 'CVE-2021-44228',
    vendor: 'Apache',
    product: 'Log4j 2',
    description: 'RCE via JNDI injection in log message lookup — Log4Shell',
    cvss: 10.0,
    cvssLabel: 'CRITICAL',
    epss: 0.97,
    nuclei: true,
    exploitDb: true,
    attackTechnique: 'T1190',
    cwe: 'CWE-917',
    vulnClass: 'Remote Code Execution',
    // World-Side: this CVE is the active demo path for the edge-appliance candidate
    worldCandidateId: 'cs-fixture-edge-appliance-001',
    // KEV metadata — kve.json row for CVE-2021-44228
    kevDateAdded: '2021-12-10',
    kevSourceProduct: 'Log4j2',
    kevDescription:
      'Apache Log4j2 contains a vulnerability where JNDI features do not protect against attacker-controlled JNDI-related endpoints, allowing for remote code execution.',
  },
  {
    rank: 2,
    cveId: 'CVE-2017-5638',
    vendor: 'Apache',
    product: 'Struts 2',
    description:
      'RCE via malformed Content-Type header in multipart parser — S2-045',
    cvss: 10.0,
    cvssLabel: 'CRITICAL',
    epss: 0.94,
    nuclei: true,
    exploitDb: true,
    attackTechnique: 'T1190',
    cwe: 'CWE-20',
    vulnClass: 'Remote Code Execution',
    worldCandidateId: null,
    // KEV metadata — kve.json row for CVE-2017-5638
    kevDateAdded: '2021-11-03',
    kevSourceProduct: 'Struts',
    kevDescription:
      'Apache Struts Jakarta Multipart parser allows for malicious file upload using the Content-Type value, leading to remote code execution.',
  },
  {
    rank: 3,
    cveId: 'CVE-2014-0160',
    vendor: 'OpenSSL',
    product: 'OpenSSL < 1.0.1g',
    description:
      'TLS heartbeat extension bounds check failure — Heartbleed information disclosure',
    cvss: 7.5,
    cvssLabel: 'HIGH',
    epss: 0.91,
    nuclei: true,
    exploitDb: true,
    attackTechnique: 'T1212',
    cwe: 'CWE-126',
    vulnClass: 'Information Disclosure',
    worldCandidateId: null,
    // KEV metadata — kve.json row for CVE-2014-0160
    kevDateAdded: '2022-05-04',
    kevSourceProduct: 'OpenSSL',
    kevDescription:
      'The TLS and DTLS implementations in OpenSSL do not properly handle Heartbeat Extension packets, which allows remote attackers to obtain sensitive information.',
  },
  {
    rank: 4,
    cveId: 'CVE-2020-1472',
    vendor: 'Microsoft',
    product: 'Netlogon',
    description:
      'Cryptographic flaw allows domain controller takeover — Zerologon',
    cvss: 10.0,
    cvssLabel: 'CRITICAL',
    epss: 0.93,
    nuclei: true,
    exploitDb: true,
    attackTechnique: 'T1068',
    cwe: 'CWE-330',
    vulnClass: 'Privilege Escalation',
    worldCandidateId: null,
    // KEV metadata — kve.json row for CVE-2020-1472
    kevDateAdded: '2021-11-03',
    kevSourceProduct: 'Netlogon',
    kevDescription:
      "Microsoft's Netlogon Remote Protocol (MS-NRPC) contains a privilege escalation vulnerability when an attacker establishes a vulnerable Netlogon secure channel connection to a domain controller. Also known as Zerologon.",
  },
  {
    rank: 5,
    cveId: 'CVE-2019-11510',
    vendor: 'Pulse Secure',
    product: 'SSL VPN',
    description: 'Pre-auth arbitrary file read exposes plaintext credentials',
    cvss: 10.0,
    cvssLabel: 'CRITICAL',
    epss: 0.95,
    nuclei: true,
    exploitDb: true,
    attackTechnique: 'T1190',
    cwe: 'CWE-22',
    vulnClass: 'Arbitrary File Read',
    worldCandidateId: null,
    // KEV metadata — kve.json row for CVE-2019-11510
    // vendorProject in kve.json is "Ivanti" (formerly Pulse Secure)
    kevDateAdded: '2021-11-03',
    kevSourceProduct: 'Pulse Connect Secure',
    kevDescription:
      'Ivanti Pulse Connect Secure contains an arbitrary file read vulnerability that allows an unauthenticated remote attacker with network access via HTTPS to send a specially crafted URI.',
  },
];
