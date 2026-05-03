$javaDir  = "C:\lab\java\jdk8u402-b06"
$labDir   = "C:\lab"
$appDir   = "$labDir\vulnerable-app"
$log4jDir = "$labDir\apache-log4j-2.14.0-bin"
$nssm     = "$labDir\nssm\nssm-2.24\win64\nssm.exe"

$cp = "$log4jDir\log4j-core-2.14.0.jar;$log4jDir\log4j-api-2.14.0.jar;$appDir"

# JVM flags — trustURLCodebase plus JDK 8u362+ factory filter bypass
$jvmFlags = "-Dcom.sun.jndi.ldap.object.trustURLCodebase=true " +
            "-Dcom.sun.jndi.rmi.object.trustURLCodebase=true " +
            "-Djdk.jndi.object.factoriesFilter=* " +
            "-Dlog4j.configurationFile=$appDir\log4j2.xml"

$appArgs  = "$jvmFlags -cp `"$cp`" VulnerableApp"

Write-Host "[*] Stopping VulnerableApp service..."
& $nssm stop VulnerableApp

Start-Sleep -Seconds 2

Write-Host "[*] Updating AppParameters..."
& $nssm set VulnerableApp AppParameters $appArgs

Write-Host "[*] Starting VulnerableApp service..."
& $nssm start VulnerableApp

Start-Sleep -Seconds 2

Write-Host "[*] Verifying process command line..."
$proc = Get-WmiObject Win32_Process | Where-Object { $_.Name -like "*java*" }
if ($proc) {
    Write-Host "[+] Java process found: $($proc.ProcessId)"
    Write-Host "[+] Command line: $($proc.CommandLine)"
} else {
    Write-Host "[-] No java process found — check service logs"
}

Write-Host ""
Write-Host "[*] Test: compile and run JNDI test..."
$javac = "$javaDir\bin\javac.exe"
$java  = "$javaDir\bin\java.exe"

if (Test-Path "C:\lab\TestJNDI.java") {
    & $javac -d C:\lab "C:\lab\TestJNDI.java"
    & $java -Dcom.sun.jndi.ldap.object.trustURLCodebase=true `
            -Djdk.jndi.object.factoriesFilter=* `
            -cp C:\lab TestJNDI
}
