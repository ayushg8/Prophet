Write-Host "=== Lab Setup Script ===" -ForegroundColor Cyan

# Task 2: Extract Java
Write-Host "[1] Extracting Java 8..." -ForegroundColor Yellow
if (Test-Path "C:\lab\java\openjdk8-alt.zip") {
    Expand-Archive "C:\lab\java\openjdk8-alt.zip" "C:\lab\java" -Force
    $javaDir = Get-ChildItem "C:\lab\java" -Directory | Select-Object -First 1
    $env:JAVA_HOME = $javaDir.FullName
    [Environment]::SetEnvironmentVariable("JAVA_HOME", $javaDir.FullName, "Machine")
    $currentPath = [Environment]::GetEnvironmentVariable("PATH","Machine")
    [Environment]::SetEnvironmentVariable("PATH", "$currentPath;$($javaDir.FullName)\bin", "Machine")
    Write-Host "  Java extracted to: $($javaDir.FullName)" -ForegroundColor Green
} else {
    Write-Host "  Java zip not found, downloading..." -ForegroundColor Yellow
    New-Item -Path "C:\lab\java" -ItemType Directory -Force | Out-Null
    curl.exe -L -o "C:\lab\java\openjdk8-alt.zip" "https://builds.openlogic.com/downloadJDK/openlogic-openjdk/8u392-b08/openlogic-openjdk-8u392-b08-windows-x64.zip"
    Expand-Archive "C:\lab\java\openjdk8-alt.zip" "C:\lab\java" -Force
    $javaDir = Get-ChildItem "C:\lab\java" -Directory | Select-Object -First 1
    $env:JAVA_HOME = $javaDir.FullName
    [Environment]::SetEnvironmentVariable("JAVA_HOME", $javaDir.FullName, "Machine")
    $currentPath = [Environment]::GetEnvironmentVariable("PATH","Machine")
    [Environment]::SetEnvironmentVariable("PATH", "$currentPath;$($javaDir.FullName)\bin", "Machine")
    Write-Host "  Java installed at: $($javaDir.FullName)" -ForegroundColor Green
}

# Find java.exe
$javaHome = [Environment]::GetEnvironmentVariable("JAVA_HOME","Machine")
$javaExe  = "$javaHome\bin\java.exe"
$javacExe = "$javaHome\bin\javac.exe"
Write-Host "  Java: $javaExe" -ForegroundColor Green
& $javaExe -version

# Task 3: Extract Log4j
Write-Host "[2] Extracting Log4j 2.14.0..." -ForegroundColor Yellow
if (Test-Path "C:\lab\log4j-2.14.0.zip") {
    Expand-Archive "C:\lab\log4j-2.14.0.zip" "C:\lab" -Force
}
$log4jDir = Get-ChildItem "C:\lab" -Directory | Where-Object { $_.Name -like "apache-log4j*" } | Select-Object -First 1
Write-Host "  Log4j at: $($log4jDir.FullName)" -ForegroundColor Green

# Task 4: Compile VulnerableApp
Write-Host "[3] Compiling VulnerableApp..." -ForegroundColor Yellow
$cp = "$($log4jDir.FullName)\log4j-core-2.14.0.jar;$($log4jDir.FullName)\log4j-api-2.14.0.jar"
& $javacExe -cp $cp "C:\lab\vulnerable-app\VulnerableApp.java" -d "C:\lab\vulnerable-app"
Write-Host "  Compiled OK" -ForegroundColor Green

# Task 5: Compile Exploit.class
Write-Host "[4] Compiling Exploit payload..." -ForegroundColor Yellow
& $javacExe "C:\lab\exploits\Exploit.java" -d "C:\lab\exploits"
Write-Host "  Compiled OK" -ForegroundColor Green

# Task 6: Download NSSM
Write-Host "[5] Downloading NSSM..." -ForegroundColor Yellow
New-Item -Path "C:\lab\nssm" -ItemType Directory -Force | Out-Null
curl.exe -L -o "C:\lab\nssm\nssm.zip" "https://nssm.cc/release/nssm-2.24.zip"
Expand-Archive "C:\lab\nssm\nssm.zip" "C:\lab\nssm" -Force
$nssmExe = Get-ChildItem "C:\lab\nssm" -Recurse -Filter "nssm.exe" | Where-Object { $_.FullName -like "*64*" } | Select-Object -First 1
Write-Host "  NSSM at: $($nssmExe.FullName)" -ForegroundColor Green

# Task 7: Install VulnerableApp as Windows service (runs as SYSTEM)
Write-Host "[6] Installing VulnerableApp as Windows service..." -ForegroundColor Yellow
$cp = "$($log4jDir.FullName)\log4j-core-2.14.0.jar;$($log4jDir.FullName)\log4j-api-2.14.0.jar;C:\lab\vulnerable-app"

# Create run script
@"
@echo off
"$javaExe" -cp "$cp" VulnerableApp
"@ | Set-Content "C:\lab\vulnerable-app\run.bat"

# Remove existing service if present
& $nssmExe.FullName stop VulnerableApp 2>$null
& $nssmExe.FullName remove VulnerableApp confirm 2>$null

# Install service
& $nssmExe.FullName install VulnerableApp "$javaExe"
& $nssmExe.FullName set VulnerableApp AppParameters "-cp `"$cp`" VulnerableApp"
& $nssmExe.FullName set VulnerableApp AppDirectory "C:\lab\vulnerable-app"
& $nssmExe.FullName set VulnerableApp ObjectName LocalSystem
& $nssmExe.FullName set VulnerableApp Start SERVICE_AUTO_START
& $nssmExe.FullName start VulnerableApp
Write-Host "  Service installed and started" -ForegroundColor Green

# Task 7b: Open firewall ports
Write-Host "[7] Opening firewall ports..." -ForegroundColor Yellow
netsh advfirewall firewall add rule name="Log4Shell HTTP" dir=in action=allow protocol=TCP localport=8080 | Out-Null
netsh advfirewall firewall add rule name="Log4Shell LDAP" dir=in action=allow protocol=TCP localport=1389 | Out-Null
netsh advfirewall firewall add rule name="Log4Shell Exploit HTTP" dir=in action=allow protocol=TCP localport=8888 | Out-Null
Write-Host "  Ports 8080, 1389, 8888 opened" -ForegroundColor Green

# Verify
Write-Host ""
Write-Host "=== VERIFICATION ===" -ForegroundColor Cyan
sc.exe query VulnerableApp | Select-String "STATE"
netstat -an | Select-String ":8080"
Write-Host ""
Write-Host "SETUP COMPLETE! Ready to demo Log4Shell." -ForegroundColor Green
Write-Host "Vulnerable app running at http://localhost:8080" -ForegroundColor Green
