/**
 * Sanitize strings before rendering to UI.
 * Replaces known sensitive substrings from the lab codebase with safe placeholders.
 * Called on any string that might contain lab artifacts.
 */

const REPLACEMENTS: [string | RegExp, string][] = [
  // Real IPs
  ['10.1.60.232', '[LAB-HOST]'],
  ['10.1.60.216', '[LLM-HOST]'],

  // Credentials
  ['sshadmin', '[OPERATOR]'],
  ['sshguest', '[GUEST]'],
  // Known lab-password shape from the burned demo credential, without
  // storing the credential literal in the public repo.
  [/exploit\s*:-\)/gi, '[REDACTED]'],
  // High-entropy placeholder-style passwords that may appear in lab output.
  [/\b[A-Za-z0-9]{20,}\b/g, '[REDACTED]'],

  // Working LDAP/exploit endpoints — allow redacted form already in use
  // but strip real ones
  [/ldap:\/\/127\.0\.0\.1:\d+\/Exploit/g, 'ldap://[REDACTED]/Exploit'],
  [/ldap:\/\/\d+\.\d+\.\d+\.\d+:\d+\/Exploit/g, 'ldap://[REDACTED]/Exploit'],

  // Raw Runtime.exec / cmd.exe payload fragments
  [/cmd\.exe \/c net localgroup administrators[^\n]*/gi, '[REDACTED PAYLOAD]'],
  [/Runtime\.getRuntime\(\)\.exec\([^\)]+\)/g, '[REDACTED EXEC]'],

  // World-Side additions — patterns scanned from stage2 fixtures and outputs.
  // The INTERFACE.md schema explicitly bans named live targets, individual
  // names, actor emails/handles, and credential paths. The fixture/output
  // files were reviewed: no live IPs, no personal credentials, no actor
  // emails, and no named-individual targets were found. The patterns below
  // are added as a defensive belt-and-suspenders layer in case any such
  // strings appear in future world-side content passed through sanitize().

  // Generic bare IPv4 addresses that are not already covered above
  [/\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b/g, '[INTERNAL-IP]'],

  // Any remaining routable IPv4 address (not loopback/private — catches
  // accidental inclusion of external C2 or staging IPs)
  [/\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b/g, '[IP-REDACTED]'],

  // Loopback LDAP/exploit endpoints (already partially covered but explicit)
  [/ldap:\/\/localhost:\d+\/[^\s"]*/g, 'ldap://[REDACTED]/[REDACTED]'],

  // Actor email or handle patterns (schema bans these; strip if present)
  [/[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}/g, '[EMAIL-REDACTED]'],
];

export function sanitize(input: string): string {
  let out = input;
  for (const [pattern, replacement] of REPLACEMENTS) {
    if (typeof pattern === 'string') {
      out = out.split(pattern).join(replacement);
    } else {
      out = out.replace(pattern, replacement);
    }
  }
  return out;
}
