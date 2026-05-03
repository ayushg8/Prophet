#!/usr/bin/env python3
"""
Qwen Agent Loop — drives exploit setup on Windows machine via SSH
Uses local Qwen 3.5 35B at 10.1.60.216:1234 as the brain
"""

import os
import subprocess, json, urllib.request, time, sys

LLM_URL   = os.environ.get("QWEN_AGENT_LLM_URL", "http://127.0.0.1:1234/v1/chat/completions")
MODEL     = os.environ.get("QWEN_AGENT_MODEL", "qwen/qwen3.5-35b-a3b")
WIN_HOST  = os.environ.get("QWEN_AGENT_WIN_HOST", "")
WIN_USER  = os.environ.get("QWEN_AGENT_WIN_USER", "")
WIN_PASS  = os.environ.get("QWEN_AGENT_WIN_PASS", "")
MAX_STEPS = 40

SYSTEM_PROMPT = """You are an autonomous Windows exploitation agent.

Your goal: Set up a working PrintNightmare (CVE-2021-34527) privilege escalation demo on a Windows machine.
The demo should let a low-privilege user (sshguest) escalate to SYSTEM.

You control the Windows machine at 10.1.60.232 via SSH (user: sshadmin, admin privileges).
The machine is currently running Windows 11 25H2 — we need to install Windows Server 2019 (unpatched) from an ISO.
The ISO will be provided at C:\\server2019.iso once downloaded.

You have one tool: run_ssh(command) — runs a cmd.exe command on the Windows machine and returns output.

Rules:
- Output ONLY valid JSON: {"thought": "...", "command": "..."} or {"thought": "...", "done": true, "summary": "..."}
- Use cmd.exe syntax (not bash). For PowerShell prefix with: powershell -Command "..."
- Check your work after each step before moving on
- If a command fails, diagnose and try a different approach
- When the exploit environment is fully ready, output done:true

Current tasks in order:
1. Check if server2019.iso exists at C:\\ and its size
2. If ISO exists and is full size (~4.9GB), mount it: powershell Mount-DiskImage
3. Run D:\\setup.exe /auto upgrade /dynamicupdate disable to install Server 2019
4. After reboot, verify OS version is Server 2019
5. Ensure SSH is still accessible
6. Download PrintNightmare PoC (cube0x0's) from GitHub
7. Compile/prepare the exploit
8. Create sshguest low-priv account if not exists
9. Test that sshguest cannot access admin resources (confirm low-priv)
10. Execute PrintNightmare as sshguest → verify SYSTEM shell achieved

Begin. Check the ISO first."""


def ssh(cmd: str) -> str:
    """Run a command on the Windows machine via SSH"""
    if not (WIN_HOST and WIN_USER and WIN_PASS):
        raise RuntimeError(
            "Set QWEN_AGENT_WIN_HOST, QWEN_AGENT_WIN_USER, and "
            "QWEN_AGENT_WIN_PASS in the local environment; never commit them."
        )
    safe_cmd = cmd.replace('"', '\\"').replace("'", "\\'")
    expect_script = f"""
set timeout 120
spawn ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 {WIN_USER}@{WIN_HOST}
expect "password:"
send "{WIN_PASS}\\r"
expect "sshadmin@"
send "{safe_cmd}\\r"
expect "sshadmin@"
send "exit\\r"
expect eof
"""
    result = subprocess.run(
        ["expect", "-c", expect_script],
        capture_output=True, text=True, timeout=150
    )
    import re
    output = re.sub(r'\x1b\[[0-9;?]*[a-zA-Z]|\][0-9];[^\x07]*\x07', '', result.stdout)
    lines = output.split('\n')
    # Find lines between the sent command and the next prompt
    capturing, out = False, []
    for line in lines:
        clean = line.strip()
        if safe_cmd[:20] in clean:
            capturing = True
            continue
        if capturing:
            if 'sshadmin@' in clean or 'exit' == clean:
                break
            if clean and 'Microsoft Windows' not in clean and '(c) Microsoft' not in clean.lower():
                out.append(clean)
    return '\n'.join(out[:30]) if out else output.strip()[-500:]


def ask_llm(messages: list) -> dict:
    """Send messages to local Qwen and get JSON response"""
    payload = json.dumps({
        "model": MODEL,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 512,
        "enable_thinking": False
    }).encode()

    req = urllib.request.Request(LLM_URL, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise ValueError(f"HTTP {e.code}: {e.read().decode()[:300]}")

    # Qwen reasoning models put output in reasoning_content when content is empty
    msg = data["choices"][0]["message"]
    content = msg.get("content", "").strip()
    if not content:
        content = msg.get("reasoning_content", "").strip()

    # Extract JSON from response (Qwen sometimes wraps in markdown)
    import re
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError(f"No JSON in response: {content[:200]}")


def main():
    print("=" * 60)
    print("Qwen Agent — PrintNightmare Setup")
    print("=" * 60)
    print(f"Target: {WIN_USER}@{WIN_HOST}")
    print(f"Model:  {MODEL}")
    print()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Begin. The ISO is NOT yet on the machine. Download it using curl with this exact URL (no auth required, direct CDN link): https://dn721605.ca.archive.org/0/items/windows-server-2019_build-17763.737/17763.737.190906-2324.rs5_release_svc_refresh_SERVER_EVAL_x64FRE_en-us_1.iso — Use curl.exe -L -o C:\\server2019.iso <url> and run it as a background job using Start-Job in PowerShell so it doesn't block. Then verify it started."}
    ]

    for step in range(1, MAX_STEPS + 1):
        print(f"\n[Step {step}/{MAX_STEPS}]", flush=True)

        try:
            response = ask_llm(messages)
        except Exception as e:
            print(f"LLM error: {e}")
            time.sleep(3)
            continue

        thought  = response.get("thought", "")
        command  = response.get("command", "")
        done     = response.get("done", False)
        summary  = response.get("summary", "")

        print(f"THINK: {thought}")

        if done:
            print(f"\n{'='*60}")
            print("AGENT DONE!")
            print(f"Summary: {summary}")
            print(f"{'='*60}")
            break

        if not command:
            print("No command returned, retrying...")
            messages.append({"role": "assistant", "content": json.dumps(response)})
            messages.append({"role": "user", "content": "Please provide a command to run."})
            continue

        print(f"  CMD: {command}")

        output = ssh(command)
        print(f"  OUT: {output[:300]}")

        # Feed result back to model
        messages.append({"role": "assistant", "content": json.dumps(response)})
        messages.append({"role": "user", "content": f"Command output:\n{output}\n\nContinue to the next step."})

        time.sleep(1)

    else:
        print(f"\nReached max steps ({MAX_STEPS}). Check current state manually.")


if __name__ == "__main__":
    main()
