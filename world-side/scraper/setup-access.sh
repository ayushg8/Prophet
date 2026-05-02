#!/usr/bin/env bash
# world-side/scraper/setup-access.sh
#
# One-shot SSH setup for teammates joining the scraper machine.
# Reads .env.local (which Ayush sends out-of-band), generates a per-user
# SSH key if missing, adds a Host block to ~/.ssh/config if missing,
# and prints the public key to send to Ayush.
#
# Idempotent — running twice is safe.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env.local"

# ---------- 1. Load .env.local ----------
if [ ! -f "$ENV_FILE" ]; then
    cat <<EOF
ERROR: $ENV_FILE not found.

Get .env.local from Ayush (Discord DM) and place it at:
    world-side/scraper/.env.local

The file is gitignored. Never commit it.
EOF
    exit 1
fi

# shellcheck disable=SC1090
source "$ENV_FILE"

# Validate required vars
missing=()
for var in SCRAPER_HOST SCRAPER_USER SCRAPER_PORT; do
    if [ -z "${!var:-}" ]; then
        missing+=("$var")
    fi
done
if [ ${#missing[@]} -gt 0 ]; then
    echo "ERROR: missing variables in $ENV_FILE: ${missing[*]}"
    echo "Ask Ayush to send a complete .env.local."
    exit 1
fi

# ---------- 2. Generate SSH key if missing ----------
KEY_PATH="${SCRAPER_KEY_PATH:-$HOME/.ssh/prophet_scraper_ed25519}"
KEY_PATH="${KEY_PATH/#\~/$HOME}"  # expand ~ if present

mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

if [ ! -f "$KEY_PATH" ]; then
    echo "Generating new ed25519 key at $KEY_PATH ..."
    ssh-keygen -t ed25519 -f "$KEY_PATH" \
        -C "prophet-scraper-$(whoami)@$(hostname -s 2>/dev/null || hostname)" \
        -N ""
    echo "Key generated."
else
    echo "Key already exists at $KEY_PATH — keeping it."
fi

# ---------- 3. Add Host block to ~/.ssh/config if missing ----------
SSH_CONFIG="$HOME/.ssh/config"
touch "$SSH_CONFIG"
chmod 600 "$SSH_CONFIG"

if grep -qE "^Host[[:space:]]+prophet-scraper([[:space:]]|$)" "$SSH_CONFIG"; then
    echo "Host prophet-scraper already in $SSH_CONFIG — not modifying."
    echo "If host/user/port changed, edit that block by hand."
else
    cat <<EOF >> "$SSH_CONFIG"

# --- Prophet scraper machine (added by world-side/scraper/setup-access.sh) ---
Host prophet-scraper
  HostName       $SCRAPER_HOST
  User           $SCRAPER_USER
  Port           $SCRAPER_PORT
  IdentityFile   $KEY_PATH
  IdentitiesOnly yes
  ServerAliveInterval 60
  ServerAliveCountMax 3
EOF
    echo "Added Host prophet-scraper block to $SSH_CONFIG"
fi

# ---------- 4. Print the public key for the teammate to share ----------
PUBKEY_PATH="${KEY_PATH}.pub"
if [ ! -f "$PUBKEY_PATH" ]; then
    echo "ERROR: public key not found at $PUBKEY_PATH (should have been generated)"
    exit 1
fi

cat <<EOF

============================================================
SETUP COMPLETE.

Send the line below to Ayush (Discord DM). It is your PUBLIC key —
safe to share. NEVER share the matching private key file.

------------------------------------------------------------
$(cat "$PUBKEY_PATH")
------------------------------------------------------------

Once Ayush adds your public key to the scraper's authorized_keys,
test the connection with:

    ssh prophet-scraper

If you see "Permission denied (publickey)", Ayush hasn't added you
yet. If you see "Connection refused", check VPN / wifi.
============================================================
EOF
