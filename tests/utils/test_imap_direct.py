"""
Direct IMAP Test - Tests all common configurations
No interactive input required
"""

import sys
from imapclient import IMAPClient
import socket

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

# Credentials from .env.production
username = "integrum@horme.com.sg"
password = "integrum2@25"

print("="*70)
print("IMAP CONFIGURATION TEST")
print("="*70)
print(f"Username: {username}")
print(f"Password: {'*' * len(password)}")
print()

# Test configurations
configurations = [
    ("mail.horme.com.sg", 993, True, "Standard cPanel SSL"),
    ("webmail.horme.com.sg", 993, True, "Webmail SSL"),
    ("horme.com.sg", 993, True, "Domain SSL"),
    ("imap.horme.com.sg", 993, True, "IMAP subdomain SSL"),
    ("mail.horme.com.sg", 143, False, "Standard cPanel TLS"),
]

working_configs = []

for server, port, use_ssl, description in configurations:
    print(f"\n{BLUE}Testing: {description}{RESET}")
    print(f"  Server: {server}:{port} (SSL={use_ssl})")

    try:
        # Test port connectivity
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((server, port))
        sock.close()

        if result != 0:
            print(f"  {RED}✗ Port not reachable{RESET}")
            continue

        print(f"  {GREEN}✓ Port reachable{RESET}")

        # Test IMAP connection
        client = IMAPClient(server, port=port, use_uid=True, ssl=use_ssl, timeout=10)
        print(f"  {GREEN}✓ IMAP client connected{RESET}")

        # Test authentication
        try:
            client.login(username, password)
            print(f"  {GREEN}✓ Authentication successful!{RESET}")

            # Test INBOX access
            client.select_folder("INBOX")
            print(f"  {GREEN}✓ INBOX accessible{RESET}")

            client.logout()

            working_configs.append((server, port, use_ssl, description))

            print(f"\n{GREEN}{'='*70}{RESET}")
            print(f"{GREEN}SUCCESS! WORKING CONFIGURATION FOUND:{RESET}")
            print(f"{GREEN}{'='*70}{RESET}")
            print(f"Server: {server}")
            print(f"Port: {port}")
            print(f"SSL: {use_ssl}")
            print(f"{GREEN}{'='*70}{RESET}")

        except Exception as e:
            print(f"  {YELLOW}✗ Authentication failed: {e}{RESET}")

    except socket.gaierror:
        print(f"  {RED}✗ Server not found (DNS){RESET}")
    except socket.timeout:
        print(f"  {RED}✗ Connection timeout{RESET}")
    except Exception as e:
        print(f"  {RED}✗ Error: {e}{RESET}")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)

if working_configs:
    print(f"{GREEN}✓ Found {len(working_configs)} working configuration(s):{RESET}\n")

    for i, (server, port, use_ssl, description) in enumerate(working_configs, 1):
        print(f"{GREEN}Configuration {i}: {description}{RESET}")
        print(f"  EMAIL_IMAP_SERVER={server}")
        print(f"  EMAIL_IMAP_PORT={port}")
        print(f"  EMAIL_USE_SSL={'true' if use_ssl else 'false'}")
        print()

    print("="*70)
    print(f"{GREEN}✓ IMAP is configured correctly{RESET}")
    print("="*70)
    sys.exit(0)

else:
    print(f"{RED}✗ No working configuration found{RESET}\n")
    print("Possible issues:")
    print("  1. Password 'integrum2@25' is incorrect")
    print("  2. IMAP not enabled for integrum@horme.com.sg")
    print("  3. Account requires app-specific password")
    print("  4. Account locked or disabled")
    print("\nNext steps:")
    print("  1. Verify password in Roundcube webmail")
    print("  2. Check cPanel → Email Accounts → Connect Devices")
    print("  3. Contact Horme IT admin for IMAP credentials")
    print("="*70)
    sys.exit(1)
