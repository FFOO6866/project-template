"""
Quick IMAP Test - Tests standard cPanel configuration
Run with: python tests/utils/quick_imap_test.py <email> <password>
"""

import sys
from imapclient import IMAPClient

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

if len(sys.argv) < 3:
    print("Usage: python tests/utils/quick_imap_test.py <email> <password>")
    print("Example: python tests/utils/quick_imap_test.py integrum@horme.com.sg yourpassword")
    sys.exit(1)

username = sys.argv[1]
password = sys.argv[2]

# Standard cPanel IMAP configuration
server = "mail.horme.com.sg"
port = 993
use_ssl = True

print("="*70)
print("QUICK IMAP TEST - Standard cPanel Configuration")
print("="*70)
print(f"\nServer: {server}")
print(f"Port: {port}")
print(f"SSL: {use_ssl}")
print(f"Username: {username}")
print("\nTesting connection...\n")

try:
    # Create IMAP client
    client = IMAPClient(server, port=port, use_uid=True, ssl=use_ssl, timeout=10)
    print(f"{GREEN}✓ Connected to server{RESET}")

    # Try login
    client.login(username, password)
    print(f"{GREEN}✓ Login successful!{RESET}")

    # List folders
    folders = client.list_folders()
    print(f"{GREEN}✓ Found {len(folders)} folders{RESET}")

    # Select INBOX
    folder_info = client.select_folder("INBOX")
    total_messages = folder_info[b'EXISTS']
    print(f"{GREEN}✓ INBOX has {total_messages} messages{RESET}")

    client.logout()

    print("\n" + "="*70)
    print(f"{GREEN}✓ SUCCESS! Use these settings:{RESET}")
    print("="*70)
    print(f"EMAIL_IMAP_SERVER=mail.horme.com.sg")
    print(f"EMAIL_IMAP_PORT=993")
    print(f"EMAIL_USERNAME={username}")
    print(f"EMAIL_PASSWORD={password}")
    print(f"EMAIL_USE_SSL=true")
    print("="*70)

    sys.exit(0)

except Exception as e:
    print(f"{RED}✗ Failed: {e}{RESET}")
    print("\n" + "="*70)
    print(f"{YELLOW}Try these alternatives:{RESET}")
    print("="*70)
    print("1. Check if password is correct")
    print("2. Try server: webmail.horme.com.sg")
    print("3. Check cPanel → Email Accounts → Connect Devices")
    print("4. Run full discovery: python tests/utils/discover_imap_settings.py")
    print("="*70)
    sys.exit(1)
