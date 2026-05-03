#!/usr/bin/env python3
"""
Log4Shell Demo Environment Status Checker
=========================================
Checks the setup status of your CISA KEV demonstration environment.
"""

import os
import subprocess
import sys
from pathlib import Path

def check_file_exists(path, description):
    """Check if a file or directory exists"""
    if Path(path).exists():
        print(f"✅ {description}: FOUND")
        return True
    else:
        print(f"❌ {description}: MISSING")
        return False

def check_service_status(service_name):
    """Check Windows service status"""
    try:
        result = subprocess.run(
            ["sc", "query", service_name],
            capture_output=True, text=True, shell=True
        )
        if "RUNNING" in result.stdout:
            print(f"✅ {service_name} Service: RUNNING")
            return True
        elif "STOPPED" in result.stdout:
            print(f"⚠️  {service_name} Service: STOPPED")
            return False
        else:
            print(f"❌ {service_name} Service: NOT FOUND")
            return False
    except:
        print(f"❌ {service_name} Service: ERROR CHECKING")
        return False

def check_port_listening(port):
    """Check if port is listening"""
    try:
        result = subprocess.run(
            ["netstat", "-an"],
            capture_output=True, text=True, shell=True
        )
        if f":{port}" in result.stdout and "LISTENING" in result.stdout:
            print(f"✅ Port {port}: LISTENING")
            return True
        else:
            print(f"❌ Port {port}: NOT LISTENING")
            return False
    except:
        print(f"❌ Port {port}: ERROR CHECKING")
        return False

def check_java_installation():
    """Check Java installation"""
    try:
        result = subprocess.run(
            ["java", "-version"],
            capture_output=True, text=True, shell=True
        )
        if result.returncode == 0:
            version_line = result.stderr.split('\n')[0] if result.stderr else "Unknown version"
            print(f"✅ Java: INSTALLED ({version_line})")
            return True
        else:
            print("❌ Java: NOT INSTALLED OR NOT IN PATH")
            return False
    except:
        print("❌ Java: NOT FOUND")
        return False

def check_connectivity():
    """Test basic network connectivity"""
    try:
        import requests
        response = requests.get("http://127.0.0.1:8080/", timeout=5)
        if response.status_code == 200:
            print("✅ Vulnerable HTTP Service: RESPONDING")
            return True
        else:
            print(f"⚠️  Vulnerable HTTP Service: RESPONDING BUT STATUS {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Vulnerable HTTP Service: NOT RESPONDING ({e})")
        return False

def main():
    print("Log4Shell CISA KEV Demonstration Environment Status")
    print("=" * 60)
    print()

    total_checks = 0
    passed_checks = 0

    print("📁 FILE SYSTEM CHECKS")
    print("-" * 30)

    checks = [
        ("C:/lab", "Lab directory"),
        ("C:/lab/vulnerable-app", "Vulnerable app directory"),
        ("C:/lab/vulnerable-app/VulnerableApp.java", "Vulnerable Java source"),
        ("C:/lab/exploits", "Exploits directory"),
        ("C:/lab/exploits/Exploit.java", "Exploit source code"),
        ("C:/lab/marshalsec", "Marshalsec directory"),
        ("C:/lab/nssm", "NSSM directory"),
        ("C:/lab/apache-log4j-2.14.0", "Log4j 2.14.0"),
    ]

    for path, desc in checks:
        total_checks += 1
        if check_file_exists(path, desc):
            passed_checks += 1

    print()
    print("☕ JAVA ENVIRONMENT")
    print("-" * 30)
    total_checks += 1
    if check_java_installation():
        passed_checks += 1

    print()
    print("🔧 SERVICES")
    print("-" * 30)
    total_checks += 1
    if check_service_status("VulnerableApp"):
        passed_checks += 1

    print()
    print("🌐 NETWORK")
    print("-" * 30)
    network_checks = [
        (8080, "HTTP"),
        (1389, "LDAP"),
        (8888, "Exploit Server")
    ]

    for port, desc in network_checks:
        total_checks += 1
        if check_port_listening(port):
            passed_checks += 1

    # Test HTTP connectivity
    total_checks += 1
    if check_connectivity():
        passed_checks += 1

    print()
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"Status: {passed_checks}/{total_checks} checks passed")

    if passed_checks == total_checks:
        print("🎉 READY FOR DEMONSTRATION!")
        print("✅ All components configured correctly")
        print("🚀 Run the exploit demonstration script")
    elif passed_checks >= total_checks * 0.8:
        print("⚠️  MOSTLY READY")
        print("🔧 Some components need attention but demo may work")
        print("📋 Check the failed items above")
    else:
        print("❌ SETUP INCOMPLETE")
        print("🛠️  Several components need configuration")
        print("📖 Review setup instructions")

    print()
    print("🎯 NEXT STEPS")
    print("-" * 30)

    if not check_file_exists("C:/lab/exploits/Exploit.class", "Compiled exploit"):
        print("1. Compile Exploit.java:")
        print("   javac C:/lab/exploits/Exploit.java")

    if not check_file_exists("C:/lab/vulnerable-app/VulnerableApp.class", "Compiled vulnerable app"):
        print("2. Compile VulnerableApp.java:")
        print("   javac -cp 'C:/lab/apache-log4j-2.14.0/log4j-*.jar' C:/lab/vulnerable-app/VulnerableApp.java")

    print("3. Start vulnerable service as LocalSystem:")
    print("   Use NSSM to wrap Java application as Windows service")

    print("4. Run demonstration:")
    print("   python demo_script.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Status check interrupted")
    except Exception as e:
        print(f"\n❌ Error during status check: {e}")